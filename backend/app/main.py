"""FastAPI application — routes and app factory.

Routes (all under /api prefix):
  GET  /api/health        — liveness check
  POST /api/convert       — convert one or more files / zips
  POST /api/convert-alt   — re-convert one file with the alternate converter
"""

import os
import shutil
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .converter import convert_file, ConvertResult, ERROR_CODES, SUPPORTED_EXTENSIONS
from .zip_utils import extract_zip

# ---------------------------------------------------------------------------
# Config from environment
# ---------------------------------------------------------------------------

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "50"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="MDConv", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

RETRYABLE_CODES = {"timeout", "memory"}
DETERMINISTIC_ERROR_CODES = set(ERROR_CODES.keys()) - RETRYABLE_CODES


def _attempt_convert(path: Path, path_in_zip: str | None, converter: str) -> ConvertResult:
    """Convert a file, auto-retrying once for retryable transient errors."""
    result = convert_file(path, path_in_zip=path_in_zip, converter=converter)
    if result.status == "error" and result.error_code in RETRYABLE_CODES:
        # One automatic retry for timeout / memory errors only
        result = convert_file(path, path_in_zip=path_in_zip, converter=converter)
    return result


def _result_to_dict(r: ConvertResult, uid: str) -> dict:
    return {
        "id": uid,
        "filename": r.filename,
        "path": r.path_in_zip,
        "source_type": r.source_type,
        "status": r.status,
        "markdown": r.markdown,
        "words": r.words,
        "tokens_est": r.tokens_est,
        "low_text": r.low_text,
        "error": r.error,
        "error_code": r.error_code,
        "converter": r.converter,
        "retryable": r.retryable,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

api_router_prefix = "/api"


@app.get(f"{api_router_prefix}/health")
async def health() -> dict:
    """Liveness check."""
    return {"status": "ok"}


@app.post(f"{api_router_prefix}/convert")
async def convert(files: list[UploadFile] = File(...)) -> JSONResponse:
    """Accept multiple files and/or zips and return conversion results."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    # Check combined upload size
    total_size = 0
    for f in files:
        # Read size without consuming the stream — peek at content-length header
        # (not always present), fallback: we'll check after saving
        pass

    results: list[dict] = []
    ok_count = error_count = skipped_count = 0

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        for upload in files:
            # Save uploaded file to temp dir
            safe_name = Path(upload.filename or "upload").name
            dest = tmp_path / safe_name
            content = await upload.read()

            # Size check
            total_size += len(content)
            if total_size > MAX_UPLOAD_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail=f"Upload exceeds the {MAX_UPLOAD_MB} MB limit",
                )

            dest.write_bytes(content)

            if safe_name.lower().endswith(".zip"):
                # Extract zip and convert each file inside
                zip_dest = tmp_path / (dest.stem + "_extracted")
                zip_dest.mkdir()
                try:
                    extracted = extract_zip(dest, zip_dest)
                except ValueError as exc:
                    # Treat the whole zip as an error
                    results.append({
                        "id": str(uuid.uuid4()),
                        "filename": safe_name,
                        "path": safe_name,
                        "source_type": "zip",
                        "status": "error",
                        "markdown": "",
                        "words": 0,
                        "tokens_est": 0,
                        "low_text": False,
                        "error": str(exc),
                        "error_code": "parse_error",
                        "converter": "none",
                        "retryable": False,
                    })
                    error_count += 1
                    continue

                for file_path in extracted:
                    rel = str(file_path.relative_to(zip_dest))
                    result = _attempt_convert(file_path, rel, "auto")
                    uid = str(uuid.uuid4())
                    results.append(_result_to_dict(result, uid))
                    if result.status == "ok":
                        ok_count += 1
                    elif result.status == "error":
                        error_count += 1
                    else:
                        skipped_count += 1
            else:
                result = _attempt_convert(dest, safe_name, "auto")
                uid = str(uuid.uuid4())
                results.append(_result_to_dict(result, uid))
                if result.status == "ok":
                    ok_count += 1
                elif result.status == "error":
                    error_count += 1
                else:
                    skipped_count += 1

    return JSONResponse({
        "results": results,
        "summary": {
            "total": len(results),
            "ok": ok_count,
            "error": error_count,
            "skipped": skipped_count,
        },
    })


@app.post(f"{api_router_prefix}/convert-alt")
async def convert_alt(
    file: UploadFile = File(...),
    converter: str = Form(...),
) -> JSONResponse:
    """Re-convert one file using the specified alternate converter."""
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    allowed_converters = {"markitdown", "pymupdf4llm"}
    if converter not in allowed_converters:
        raise HTTPException(status_code=400, detail=f"Unknown converter '{converter}'")

    ext = Path(file.filename or "").suffix.lower()
    if converter == "pymupdf4llm" and ext != ".pdf":
        raise HTTPException(
            status_code=415,
            detail="pymupdf4llm only supports PDF files",
        )

    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / (file.filename or "upload")
        content = await file.read()

        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="File too large")

        dest.write_bytes(content)
        result = convert_file(dest, path_in_zip=file.filename, converter=converter)

    return JSONResponse(_result_to_dict(result, str(uuid.uuid4())))


# ---------------------------------------------------------------------------
# Serve built frontend (production / Docker)
# ---------------------------------------------------------------------------

_static_dir = Path(__file__).parent / "static"
if _static_dir.exists():
    app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="static")

