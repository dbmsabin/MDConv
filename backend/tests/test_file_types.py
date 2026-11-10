import io
import zipfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.converter import convert_file
import fitz  # PyMuPDF
from pptx import Presentation

client = TestClient(app)


def test_convert_pdf(tmp_path: Path):
    # Generate a simple valid PDF using fitz
    pdf_path = tmp_path / "document.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), "This is a test PDF document with important text.")
    doc.save(str(pdf_path))
    doc.close()

    result = convert_file(pdf_path)
    assert result.status == "ok"
    assert result.source_type == "pdf"
    assert "test PDF document" in result.markdown
    assert result.words > 0


def test_convert_pptx(tmp_path: Path):
    # Generate a simple valid PPTX using python-pptx
    pptx_path = tmp_path / "presentation.pptx"
    prs = Presentation()
    slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    subtitle = slide.placeholders[1]
    title.text = "Hello Presentation"
    subtitle.text = "Slide subtitle content"
    prs.save(str(pptx_path))

    result = convert_file(pptx_path)
    assert result.status == "ok"
    assert result.source_type == "pptx"
    assert "Hello Presentation" in result.markdown


def test_convert_docx(tmp_path: Path):
    # Generate a minimal docx (which is a zip package containing word/document.xml)
    docx_path = tmp_path / "document.docx"
    doc_xml = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
      <w:body>
        <w:p><w:r><w:t>Hello from real DOCX test file!</w:t></w:r></w:p>
      </w:body>
    </w:document>"""
    content_types = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
      <Default Extension="xml" ContentType="application/xml"/>
      <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
    </Types>"""
    rels = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
      <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
    </Relationships>"""

    with zipfile.ZipFile(docx_path, "w") as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("word/document.xml", doc_xml)

    result = convert_file(docx_path)
    assert result.status == "ok"
    assert result.source_type == "docx"
    assert "Hello from real DOCX test file" in result.markdown


def test_convert_corrupt_file(tmp_path: Path):
    corrupt_docx = tmp_path / "corrupt.docx"
    corrupt_docx.write_bytes(b"PK\x03\x04\x00\x00corrupted_non_zip_file_data\xff\xfe")

    result = convert_file(corrupt_docx)
    assert result.status == "error"
    assert result.error_code == "parse_error"
    assert result.retryable is True
