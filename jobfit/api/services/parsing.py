from __future__ import annotations

from pathlib import Path
from typing import Dict, List
import re

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

def _normalize_lines(text: str) -> List[str]:
    """
    Normalize odd spacing from PDFs and join mid-sentence hard wraps.
    """
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"[ \t]+", " ", t)
    lines = [ln.strip() for ln in t.split("\n")]
    out: List[str] = []
    buf = ""
    for ln in lines:
        if not ln:
            if buf:
                out.append(buf.strip())
                buf = ""
            out.append("")  # keep blank line as a boundary
            continue
        if buf:
            # If previous line ends a sentence or current line starts uppercase, break
            if END_PUNCT.search(buf) or ln[:1].isupper():
                out.append(buf.strip())
                buf = ln
            else:
                buf += " " + ln
        else:
            buf = ln
    if buf:
        out.append(buf.strip())
    return out

def _is_bullet_line(ln: str) -> bool:
    s = ln.lstrip()
    return s[:1] in BULLET_MARKERS or bool(re.match(r"^[\-\*\u2022•·]\s+", s))

def _strip_bullet_prefix(s: str) -> str:
    return re.sub(r"^([\-\*\u2022•·]|–)\s*", "", s).strip()

def _looks_like_fragment(s: str) -> bool:
    """
    Heuristic: a fragment is very short, has no ending punctuation,
    and is typically 1–3 words (this is what happens with 'every word bullet' PDFs).
    """
    if not s:
        return False
    if END_PUNCT.search(s):
        return False
    # treat emails/phones/domains as single tokens to keep them intact
    if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+", s):
        return True
    words = s.split()
    return len(words) <= 3 and len(s) <= 20

def split_cv(text: str) -> Dict[str, List[Dict[str, List[str]]]]:
    """
    Heuristic CV splitter for a quick on-screen preview:
      - Detects common section headings
      - Groups bullet lines
      - **Merges 'per-word bullets'** into a single bullet using a fragment accumulator
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

    # Accumulate tiny fragments like: "Product" "Executive" "|" "Data-Driven" ...
    frag_acc: List[str] = []

    def flush_frag_acc():
        """Join accumulated fragments into one bullet."""
        nonlocal frag_acc
        if frag_acc:
            joined = " ".join(frag_acc)
            # normalize stray spaces around pipes and punctuation
            joined = re.sub(r"\s*\|\s*", " | ", joined)
            joined = re.sub(r"\s{2,}", " ", joined).strip()
            if joined:
                current["bullets"].append(joined)
            frag_acc = []

    def flush_buffer_as_bullets():
        nonlocal buffer
        if not buffer:
            return
        for ln in buffer:
            s = _strip_bullet_prefix(ln)
            if _looks_like_fragment(s):
                frag_acc.append(s)
            else:
                flush_frag_acc()
                if s:
                    current["bullets"].append(s)
        buffer = []
        flush_frag_acc()

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
            current["bullets"].append(s)
        else:
            buffer.append(stripped)

    flush_buffer_as_bullets()
    if current["bullets"]:
        sections.append({"name": current["name"], "bullets": current["bullets"]})

    return {"sections": sections}
