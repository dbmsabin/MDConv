import io
import zipfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.converter import convert_file, _count_words, _tokens_est, _low_text
from app.zip_utils import extract_zip, _is_junk, _safe_path

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_zip_junk_detection():
    assert _is_junk("__MACOSX/._test.txt") is True
    assert _is_junk("folder/.DS_Store") is True
    assert _is_junk("Thumbs.db") is True
    assert _is_junk(".hidden_file") is True
    assert _is_junk("normal_file.txt") is False
    assert _is_junk("sub/folder/file.pdf") is False


def test_zip_safe_path(tmp_path: Path):
    dest = tmp_path / "out"
    dest.mkdir()

    safe = _safe_path("sub/test.txt", dest)
    assert safe is not None
    assert str(safe).startswith(str(dest))

    # Zip slip attempt
    unsafe = _safe_path("../evil.txt", dest)
    assert unsafe is None

    unsafe_abs = _safe_path("/etc/passwd", dest)
    assert unsafe_abs is None or not str(unsafe_abs).startswith("/etc")


def test_zip_extraction(tmp_path: Path):
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("test1.txt", "Hello world from test 1")
        zf.writestr("folder/test2.txt", "Hello from subfolder")
        zf.writestr("__MACOSX/._test1.txt", "junk")
        zf.writestr(".DS_Store", "junk")

    dest = tmp_path / "extracted"
    dest.mkdir()
    extracted = extract_zip(zip_path, dest)

    extracted_names = [p.name for p in extracted]
    assert "test1.txt" in extracted_names
    assert "test2.txt" in extracted_names
    assert "._test1.txt" not in extracted_names
    assert ".DS_Store" not in extracted_names


def test_converter_helpers():
    text = "One two three four five"
    assert _count_words(text) == 5
    assert _tokens_est(text) == len(text) // 4
    assert _low_text(10, "pdf") is True
    assert _low_text(100, "pdf") is False
    assert _low_text(5, "txt") is False


def test_convert_txt_file(tmp_path: Path):
    txt_file = tmp_path / "sample.txt"
    txt_file.write_text("This is a simple plain text file for testing.", encoding="utf-8")

    result = convert_file(txt_file)
    assert result.status == "ok"
    assert "simple plain text" in result.markdown
    assert result.words > 0
    assert result.source_type == "txt"


def test_convert_empty_file(tmp_path: Path):
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("", encoding="utf-8")

    result = convert_file(empty_file)
    assert result.status == "error"
    assert result.error_code == "empty"
    assert result.retryable is False


def test_convert_unsupported_file(tmp_path: Path):
    exe_file = tmp_path / "app.exe"
    exe_file.write_bytes(b"MZ\x90\x00")

    result = convert_file(exe_file)
    assert result.status == "skipped"
    assert result.error_code == "unsupported"
    assert result.retryable is False


def test_api_convert_files(tmp_path: Path):
    file1 = ("files", ("note.txt", io.BytesIO(b"# Hello\nThis is markdown test."), "text/plain"))
    file2 = ("files", ("unknown.bin", io.BytesIO(b"\x00\x01\x02"), "application/octet-stream"))

    response = client.post("/api/convert", files=[file1, file2])
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "summary" in data
    assert data["summary"]["total"] == 2
    assert data["summary"]["ok"] >= 1


def test_api_convert_zip(tmp_path: Path):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("inside.txt", "Content inside zip file.")
    zip_buffer.seek(0)

    response = client.post(
        "/api/convert",
        files=[("files", ("archive.zip", zip_buffer, "application/zip"))],
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["filename"] == "inside.txt"
    assert data["results"][0]["status"] == "ok"


def test_api_convert_alt_txt():
    # Calling convert-alt with txt should succeed with markitdown
    file_payload = ("file", ("sample.txt", io.BytesIO(b"Alternate test content"), "text/plain"))
    response = client.post(
        "/api/convert-alt",
        files=[file_payload],
        data={"converter": "markitdown"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "Alternate test content" in data["markdown"]


def test_api_convert_alt_invalid_converter():
    file_payload = ("file", ("sample.txt", io.BytesIO(b"Hello"), "text/plain"))
    response = client.post(
        "/api/convert-alt",
        files=[file_payload],
        data={"converter": "invalid_converter"},
    )
    assert response.status_code == 400


def test_api_convert_alt_pymupdf_on_non_pdf():
    file_payload = ("file", ("sample.txt", io.BytesIO(b"Hello"), "text/plain"))
    response = client.post(
        "/api/convert-alt",
        files=[file_payload],
        data={"converter": "pymupdf4llm"},
    )
    assert response.status_code == 415

