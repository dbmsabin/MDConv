"""File-to-Markdown conversion logic.

Primary converter: MarkItDown (supports docx, pdf, pptx, xlsx, html, csv, txt, …).
PDF fallback:      pymupdf4llm — used automatically when MarkItDown returns
                   near-empty output for a PDF.

Public interface
----------------
convert_file(path: Path, converter: str = "auto") -> ConvertResult
"""

import re
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class ConvertResult:
    filename: str
    path_in_zip: str          # relative path inside zip, or just filename
    source_type: str          # extension without dot, e.g. "pdf"
    status: str               # "ok" | "error" | "skipped"
    markdown: str
    words: int
    tokens_est: int
    low_text: bool
    error: str | None
    error_code: str | None    # see ERROR_CODES below
    converter: str            # "markitdown" | "pymupdf4llm"
    retryable: bool


# ---------------------------------------------------------------------------
# Supported types & error codes
# ---------------------------------------------------------------------------

SUPPORTED_EXTENSIONS = {
    ".docx", ".doc",
    ".pdf",
    ".pptx", ".ppt",
    ".xlsx", ".xls",
    ".html", ".htm",
    ".csv",
    ".txt", ".md",
}

ERROR_CODES: dict[str, tuple[str, bool]] = {
    # code            -> (human readable reason,  retryable)
    "unsupported":    ("File type not supported", False),
    "parse_error":    ("Could not read file — it may be corrupt or encrypted", True),
    "empty":          ("File appears to be empty", False),
    "timeout":        ("Conversion timed out", True),
    "memory":         ("Not enough memory to convert this file", True),
    "unknown":        ("Unexpected error during conversion", True),
}

# Near-empty threshold: if MarkItDown returns fewer chars than this for a PDF
# we fall back to pymupdf4llm.
_PDF_FALLBACK_THRESHOLD = 100
# Low-text warning: flag when word count is below this for non-trivial files
_LOW_TEXT_WORDS = 50


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _count_words(text: str) -> int:
    return len(re.findall(r"\S+", text))


def _tokens_est(text: str) -> int:
    return len(text) // 4


def _low_text(words: int, source_type: str) -> bool:
    """Flag files that have suspiciously few words (likely scanned PDFs)."""
    if source_type in ("txt", "md", "csv"):
        return False
    return words < _LOW_TEXT_WORDS


def _run_markitdown(path: Path) -> str:
    """Run MarkItDown and return the markdown string."""
    from markitdown import MarkItDown  # lazy import — large dependency
    md = MarkItDown()
    result = md.convert(str(path))
    return result.text_content or ""


def _run_pymupdf4llm(path: Path) -> str:
    """Run pymupdf4llm on a PDF and return markdown."""
    import pymupdf4llm  # lazy import
    return pymupdf4llm.to_markdown(str(path))


def _build_result(
    *,
    filename: str,
    path_in_zip: str,
    source_type: str,
    markdown: str,
    converter: str,
) -> ConvertResult:
    words = _count_words(markdown)
    return ConvertResult(
        filename=filename,
        path_in_zip=path_in_zip,
        source_type=source_type,
        status="ok",
        markdown=markdown,
        words=words,
        tokens_est=_tokens_est(markdown),
        low_text=_low_text(words, source_type),
        error=None,
        error_code=None,
        converter=converter,
        retryable=False,
    )


def _error_result(
    *,
    filename: str,
    path_in_zip: str,
    source_type: str,
    error_code: str,
    exc: Exception | None = None,
    converter: str = "markitdown",
) -> ConvertResult:
    reason, retryable = ERROR_CODES.get(error_code, ERROR_CODES["unknown"])
    return ConvertResult(
        filename=filename,
        path_in_zip=path_in_zip,
        source_type=source_type,
        status="error",
        markdown="",
        words=0,
        tokens_est=0,
        low_text=False,
        error=reason,
        error_code=error_code,
        converter=converter,
        retryable=retryable,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def convert_file(
    path: Path,
    *,
    path_in_zip: str | None = None,
    converter: str = "auto",
) -> ConvertResult:
    """Convert *path* to Markdown and return a :class:`ConvertResult`.

    Args:
        path: Absolute path to the file on disk.
        path_in_zip: Relative path as it appeared inside the zip (for display).
                     Defaults to the bare filename.
        converter: ``"auto"`` lets this function choose the best converter.
                   ``"markitdown"`` forces MarkItDown.
                   ``"pymupdf4llm"`` forces the PDF fallback (PDF only).
    """
    filename = path.name
    display_path = path_in_zip or filename
    ext = path.suffix.lower()
    source_type = ext.lstrip(".")

    # -- Unsupported file type -----------------------------------------------
    if ext not in SUPPORTED_EXTENSIONS:
        return ConvertResult(
            filename=filename,
            path_in_zip=display_path,
            source_type=source_type,
            status="skipped",
            markdown="",
            words=0,
            tokens_est=0,
            low_text=False,
            error=f"File type '{ext}' is not supported",
            error_code="unsupported",
            converter="none",
            retryable=False,
        )

    # -- Empty file -----------------------------------------------------------
    if path.stat().st_size == 0:
        return _error_result(
            filename=filename,
            path_in_zip=display_path,
            source_type=source_type,
            error_code="empty",
        )

    # -- Force pymupdf4llm ---------------------------------------------------
    if converter == "pymupdf4llm":
        if ext != ".pdf":
            return _error_result(
                filename=filename,
                path_in_zip=display_path,
                source_type=source_type,
                error_code="unsupported",
                converter="pymupdf4llm",
            )
        try:
            md = _run_pymupdf4llm(path)
            return _build_result(
                filename=filename,
                path_in_zip=display_path,
                source_type=source_type,
                markdown=md,
                converter="pymupdf4llm",
            )
        except Exception as exc:
            return _error_result(
                filename=filename,
                path_in_zip=display_path,
                source_type=source_type,
                error_code="parse_error",
                exc=exc,
                converter="pymupdf4llm",
            )

    # -- MarkItDown (default / forced) ----------------------------------------
    try:
        md = _run_markitdown(path)
    except MemoryError as exc:
        return _error_result(
            filename=filename,
            path_in_zip=display_path,
            source_type=source_type,
            error_code="memory",
            exc=exc,
        )
    except Exception as exc:
        if converter == "auto" and ext == ".pdf":
            try:
                md_fallback = _run_pymupdf4llm(path)
                if md_fallback.strip():
                    return _build_result(
                        filename=filename,
                        path_in_zip=display_path,
                        source_type=source_type,
                        markdown=md_fallback,
                        converter="pymupdf4llm",
                    )
            except Exception:
                pass
        return _error_result(
            filename=filename,
            path_in_zip=display_path,
            source_type=source_type,
            error_code="parse_error",
            exc=exc,
        )

    # -- PDF near-empty fallback (auto mode only) ----------------------------
    if converter == "auto" and ext == ".pdf" and len(md.strip()) < _PDF_FALLBACK_THRESHOLD:
        try:
            md_fallback = _run_pymupdf4llm(path)
            if md_fallback.strip():
                return _build_result(
                    filename=filename,
                    path_in_zip=display_path,
                    source_type=source_type,
                    markdown=md_fallback,
                    converter="pymupdf4llm",
                )
        except Exception:
            pass  # stay with MarkItDown result

    return _build_result(
        filename=filename,
        path_in_zip=display_path,
        source_type=source_type,
        markdown=md,
        converter="markitdown",
    )

