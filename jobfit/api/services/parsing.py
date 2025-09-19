from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

# -------- PDF -> text -------------------------------------------------

def read_pdf_text(path: Path) -> str:
    """
    Extract plain text from a PDF.
    Tries PyMuPDF (fast & robust). Falls back to pypdf if PyMuPDF isn't available.
    """
    try:
        import fitz  # PyMuPDF
        text_parts: list[str] = []
        with fitz.open(str(path)) as doc:
            for page in doc:
                text_parts.append(page.get_text("text"))
        return "\n".join(text_parts)
    except Exception:
        # Fallback to pypdf
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            out: list[str] = []
            for page in reader.pages:
                out.append(page.extract_text() or "")
            return "\n".join(out)
        except Exception as e:  # pragma: no cover
            raise RuntimeError(f"Failed to read PDF: {e}") from e

# -------- DOCX -> text -----------------------------------------------

def read_docx_text(path: Path) -> str:
    """
    Extract plain text from a DOCX file using python-docx.
    """
    try:
        from docx import Document
    except Exception as e:
        raise RuntimeError("python-docx not installed") from e

    doc = Document(str(path))
    paras = [p.text for p in doc.paragraphs]
    return "\n".join(paras)

# -------- Transcript splitting ---------------------------------------

def split_transcript(text: str) -> List[str]:
    """
    Split interview transcripts / notes into paragraphs.
    Collapses extra whitespace and drops empty blocks.
    """
    # Normalize newlines and whitespace
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    # Split on blank lines (two+ newlines)
    raw_blocks = re.split(r"\n\s*\n", t)
    blocks = [re.sub(r"\s+", " ", blk).strip() for blk in raw_blocks]
    return [b for b in blocks if b]

# -------- CV splitting (lightweight preview) -------------------------

BULLET_MARKERS = ("•", "-", "–", "*", "·")
END_PUNCT = re.compile(r"[.!?…]$")

INLINE_BULLET_CHARS = "".join(ch for ch in BULLET_MARKERS if ch != "-")
INLINE_BULLET_PATTERN = re.compile(rf"\s*[{re.escape(INLINE_BULLET_CHARS)}]\s*")


def _is_bullet_line(ln: str) -> bool:
    s = ln.lstrip()
    return s[:1] in BULLET_MARKERS or bool(re.match(r"^[\-\*\u2022•·]\s+", s))


def _normalize_lines(text: str) -> List[str]:
    """Normalize odd spacing from PDFs while keeping headings/bullets separate."""

    t = text.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"[ \t]+", " ", t)
    raw_lines = t.split("\n")

    out: List[str] = []
    buf = ""

    for raw in raw_lines:
        ln = raw.strip()
        if not ln:
            if buf:
                out.append(buf.strip())
                buf = ""
            out.append("")
            continue

        if _is_bullet_line(ln):
            if buf:
                out.append(buf.strip())
                buf = ""
            out.append(ln)
            continue

        if buf:
            starts_upper = ln[:1].isupper()
            if END_PUNCT.search(buf) or (starts_upper and not buf.endswith(":")):
                out.append(buf.strip())
                buf = ln
            else:
                buf += " " + ln
        else:
            buf = ln

    if buf:
        out.append(buf.strip())

    return out

def _strip_bullet_prefix(s: str) -> str:
    return re.sub(r"^([\-\*\u2022•·]|–)\s*", "", s).strip()


def _combine_parts(parts: List[str]) -> str:
    text = " ".join(parts)
    text = re.sub(r"\s*\|\s*", " | ", text)
    text = re.sub(r"\s*\/\s*", " / ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def _split_inline_segments(segments: List[str]) -> List[str]:
    bullets: List[str] = []
    current: List[str] = []

    def flush() -> None:
        if not current:
            return
        combined = _combine_parts(current)
        if combined:
            bullets.append(combined)
        current.clear()

    for index, segment in enumerate(segments):
        if not segment:
            continue
        if segment == "|":
            flush()
            continue

        current.append(segment)

        next_segment = segments[index + 1] if index + 1 < len(segments) else None
        if not next_segment:
            continue
        if next_segment == "|":
            flush()
            continue
        if len(current) >= 2:
            last = current[-1]
            if last[:1].isupper() and next_segment[:1].isupper():
                flush()

    flush()
    return bullets


def _normalize_bullet_text(text: str) -> List[str]:
    cleaned = text.strip()
    if not cleaned:
        return []

    if INLINE_BULLET_PATTERN.search(cleaned):
        segments = [segment.strip() for segment in INLINE_BULLET_PATTERN.split(cleaned) if segment.strip()]
        split_segments = _split_inline_segments(segments)
        if len(split_segments) >= 2:
            return split_segments
        if segments:
            cleaned = " ".join(segments)
        cleaned = INLINE_BULLET_PATTERN.sub(" ", cleaned)

    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return [cleaned] if cleaned else []


def _append_bullet(target: List[str], text: str) -> None:
    for bullet in _normalize_bullet_text(text):
        target.append(bullet)

def split_cv(text: str) -> Dict[str, List[Dict[str, List[str]]]]:
    """
    Heuristic CV splitter for a quick on-screen preview:
      - Detects common section headings
      - Groups bullet lines and their wrapped fragments together
      - Keeps short skill lists as separate bullets
    """
    lines = _normalize_lines(text)

    SECTION_HEADINGS = [
        "summary", "professional summary", "profile",
        "experience", "work experience", "professional experience",
        "skills", "core competencies", "competencies",
        "education", "certifications", "projects",
    ]

    sections: List[Dict[str, List[str]]] = []
    current = {"name": "Summary", "bullets": []}
    buffer: List[str] = []

    def flush_buffer_as_bullets():
        nonlocal buffer
        if not buffer:
            return
        parts: List[str] = []
        for ln in buffer:
            stripped = ln.strip()
            is_bullet = _is_bullet_line(stripped)
            text = _strip_bullet_prefix(stripped)
            if is_bullet:
                if parts:
                    combined = _combine_parts(parts)
                    if combined:
                        _append_bullet(current["bullets"], combined)
                parts = [text] if text else []
                continue

            if not text:
                continue

            if parts:
                parts.append(text)
            else:
                parts = [text]

        if parts:
            combined = _combine_parts(parts)
            if combined:
                _append_bullet(current["bullets"], combined)

        buffer = []

    for ln in lines:
        stripped = ln.strip()
        low = stripped.lower()

        if not stripped:
            flush_buffer_as_bullets()
            continue

        # Heading detection (beginning of line)
        if any(re.match(rf"^{re.escape(h)}\b", low) for h in SECTION_HEADINGS):
            flush_buffer_as_bullets()
            if current["bullets"]:
                sections.append({"name": current["name"], "bullets": current["bullets"]})
            # Keep the exact heading text as section name
            current = {"name": stripped, "bullets": []}
            continue

        # Bullet detection
        if _is_bullet_line(stripped):
            buffer.append(stripped)
            continue

        # Non-bullet: treat long lines as single bullets; short ones are merged
        s = stripped
        if len(s) > 40 or END_PUNCT.search(s):
            flush_buffer_as_bullets()
            _append_bullet(current["bullets"], s)
        else:
            buffer.append(stripped)

    flush_buffer_as_bullets()
    if current["bullets"]:
        sections.append({"name": current["name"], "bullets": current["bullets"]})

    return {"sections": sections}
