from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from pypdf import PdfReader


def read_pdf_text(file_path: str | Path) -> str:
    reader = PdfReader(str(file_path))
    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        parts.append(text)
    return "\n".join(parts).strip()


def read_docx_text(file_path: str | Path) -> str:
    document = Document(str(file_path))
    paragraphs = [paragraph.text for paragraph in document.paragraphs]
    return "\n".join(paragraphs).strip()


SECTION_HEADERS = {"summary", "skills", "experience", "education", "projects"}
BULLET_PATTERN = re.compile(r"^[\-\*•]\s*(.+)")


def split_cv(text: str) -> dict[str, list[dict[str, list[str]]]]:
    sections: list[dict[str, list[str]]] = []
    current_section: dict[str, list[str]] | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        heading = line.rstrip(":").strip()
        if heading.lower() in SECTION_HEADERS:
            if current_section:
                sections.append(current_section)
            current_section = {"name": heading, "bullets": []}
            continue

        bullet_match = BULLET_PATTERN.match(line)
        if bullet_match:
            bullet_text = bullet_match.group(1).strip()
            if not current_section:
                current_section = {"name": "Summary", "bullets": []}
            current_section["bullets"].append(bullet_text)
            continue

        if not current_section:
            current_section = {"name": "Summary", "bullets": []}
        current_section["bullets"].append(line)

    if current_section:
        sections.append(current_section)

    if not sections:
        paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", text) if paragraph.strip()]
        if paragraphs:
            sections = [{"name": "Summary", "bullets": paragraphs}]

    return {"sections": sections}


def split_transcript(text: str) -> list[str]:
    paragraphs: list[str] = []
    buffer: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if buffer:
                paragraphs.append(" ".join(buffer))
                buffer = []
            continue
        buffer.append(line)

    if buffer:
        paragraphs.append(" ".join(buffer))

    return paragraphs
