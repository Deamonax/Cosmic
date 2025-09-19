import io

from docx import Document
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def build_docx(paragraphs: list[str]) -> bytes:
    buffer = io.BytesIO()
    document = Document()
    for text in paragraphs:
        document.add_paragraph(text)
    document.save(buffer)
    buffer.seek(0)
    return buffer.read()


def test_upload_cv_docx_returns_preview():
    doc_bytes = build_docx([
        "Summary",
        "- Experienced software engineer",
        "Experience",
        "- Built APIs",
    ])
    files = {
        "cv_file": (
            "sample.docx",
            doc_bytes,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }
    response = client.post("/upload/cv", files=files, data={"candidate_id": "demo"})
    assert response.status_code == 200
    body = response.json()
    assert body["saved"] is True
    assert body["cv_preview"]["sections"]


def test_upload_transcript_text_file():
    files = [
        (
            "transcripts",
            (
                "notes.txt",
                b"Paragraph one.\n\nParagraph two.",
                "text/plain",
            ),
        )
    ]
    response = client.post("/upload/context", files=files, data={"candidate_id": "demo"})
    assert response.status_code == 200
    body = response.json()
    assert body["saved"] is True
    assert body["paragraph_counts"]
    assert body["paragraph_counts"][0] > 0


def test_upload_context_with_notes_only():
    response = client.post(
        "/upload/context",
        data={"candidate_id": "demo", "notes": "Follow up soon."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["saved"] is True
    assert body["sources"]
    assert body["sources"][0]["filename"] == "notes.txt"
    assert body["paragraph_counts"] == [1]


def test_upload_rejects_invalid_mimetype():
    files = {"cv_file": ("image.png", b"fake", "image/png")}
    response = client.post("/upload/cv", files=files)
    assert response.status_code == 400
