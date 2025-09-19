from __future__ import annotations

import hashlib
import unicodedata
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db import get_session
from models import Chunk, Source
from services.parsing import read_docx_text, read_pdf_text, split_cv, split_transcript

MAX_UPLOAD_BYTES = 8 * 1024 * 1024
STORAGE_DIR = Path(__file__).resolve().parent.parent / "storage"

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
ALLOWED_CV_MIME_TYPES = {"application/pdf", DOCX_MIME}
ALLOWED_TRANSCRIPT_MIME_TYPES = {"application/pdf", DOCX_MIME, "text/plain"}

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]


class CVSection(BaseModel):
    name: str
    bullets: list[str] = Field(default_factory=list)


class CVPreview(BaseModel):
    sections: list[CVSection] = Field(default_factory=list)


class CVUploadResponse(BaseModel):
    source_id: str
    cv_preview: CVPreview
    saved: bool


class SourceInfo(BaseModel):
    id: str
    filename: str


class ContextUploadResponse(BaseModel):
    sources: list[SourceInfo]
    paragraph_counts: list[int]
    saved: bool


from datetime import datetime


class SourceSummary(BaseModel):
    id: str
    filename: str
    type: str
    mimetype: str | None = None
    bytes: int
    created_at: datetime
    chunk_count: int


class SourceListResponse(BaseModel):
    sources: list[SourceSummary]


def sanitize_filename(filename: str | None) -> str:
    if not filename:
        return "upload"
    name = Path(filename).name
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = normalized.encode("ascii", "ignore").decode() or name
    safe = "".join(char for char in ascii_name if char.isalnum() or char in {".", "_", "-"})
    safe = safe.strip(".")
    return safe or "upload"


async def save_upload(file: UploadFile, target_name: str) -> tuple[Path, bytes, str]:
    content = await file.read()
    size = len(content)
    if size > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large (max 8 MB)",
        )
    safe_name = sanitize_filename(file.filename)
    filename = f"{target_name}_{safe_name}"
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    destination = STORAGE_DIR / filename
    with open(destination, "wb") as output:
        output.write(content)
    return destination, content, safe_name


def checksum_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_text(path: Path, mimetype: str, raw_bytes: bytes) -> str:
    if mimetype == "application/pdf":
        return read_pdf_text(path)
    if mimetype == DOCX_MIME:
        return read_docx_text(path)
    if mimetype == "text/plain":
        return raw_bytes.decode("utf-8", errors="ignore")
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type")


@router.post("/cv", response_model=CVUploadResponse)
async def upload_cv(
    session: SessionDep,
    cv_file: Annotated[UploadFile, File()],          # required, no default here
    candidate_id: Annotated[str, Form()] = "demo",   # default goes after '='
):
    if cv_file.content_type not in ALLOWED_CV_MIME_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported CV file type")

    source_id = str(uuid4())
    storage_path, raw_bytes, safe_name = await save_upload(cv_file, source_id)
    checksum = checksum_bytes(raw_bytes)
    candidate = candidate_id or "demo"

    try:
        text = extract_text(storage_path, cv_file.content_type, raw_bytes)
    except Exception as exc:  # pragma: no cover - unexpected read issues
        if storage_path.exists():
            storage_path.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to read CV file") from exc

    preview_dict = split_cv(text)
    preview = CVPreview.model_validate(preview_dict)

    source = Source(
        id=source_id,
        candidate_id=candidate,
        type="cv",
        filename=safe_name,
        path=str(storage_path),
        mimetype=cv_file.content_type,
        bytes=len(raw_bytes),
        checksum=checksum,
    )
    session.add(source)

    for section_index, section in enumerate(preview.sections):
        section_chunk = Chunk(
            id=str(uuid4()),
            source_id=source_id,
            kind="section",
            text=section.name,
            meta={"section_name": section.name, "order": section_index},
        )
        session.add(section_chunk)
        for bullet_index, bullet in enumerate(section.bullets):
            bullet_chunk = Chunk(
                id=str(uuid4()),
                source_id=source_id,
                kind="bullet",
                text=bullet,
                meta={"section_name": section.name, "order": bullet_index},
            )
            session.add(bullet_chunk)

    session.commit()

    return CVUploadResponse(source_id=source_id, cv_preview=preview, saved=True)


@router.post("/context", response_model=ContextUploadResponse)
async def upload_context(
    session: SessionDep,
    transcripts: Annotated[list[UploadFile] | None, File()] = File(default=None),
    notes: Annotated[str | None, Form()] = Form(default=None),
    candidate_id: Annotated[str, Form()] = Form(default="demo"),
):
    files = transcripts or []
    text_note = (notes or "").strip()
    if not files and not text_note:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide transcripts or notes")

    candidate = candidate_id or "demo"
    saved_sources: list[SourceInfo] = []
    paragraph_counts: list[int] = []

    for upload in files:
        if upload.content_type not in ALLOWED_TRANSCRIPT_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported transcript file type: {upload.content_type}",
            )
        source_id = str(uuid4())
        storage_path, raw_bytes, safe_name = await save_upload(upload, source_id)
        checksum = checksum_bytes(raw_bytes)
        try:
            text = extract_text(storage_path, upload.content_type or "", raw_bytes)
        except Exception as exc:  # pragma: no cover - unexpected read issues
            if storage_path.exists():
                storage_path.unlink(missing_ok=True)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to read transcript") from exc

        paragraphs = split_transcript(text)

        source = Source(
            id=source_id,
            candidate_id=candidate,
            type="transcript",
            filename=safe_name,
            path=str(storage_path),
            mimetype=upload.content_type,
            bytes=len(raw_bytes),
            checksum=checksum,
        )
        session.add(source)
        for index, paragraph in enumerate(paragraphs):
            chunk = Chunk(
                id=str(uuid4()),
                source_id=source_id,
                kind="paragraph",
                text=paragraph,
                meta={"order": index},
            )
            session.add(chunk)

        saved_sources.append(SourceInfo(id=source_id, filename=safe_name))
        paragraph_counts.append(len(paragraphs))

    if text_note:
        note_bytes = text_note.encode("utf-8")
        source_id = str(uuid4())
        checksum = checksum_bytes(note_bytes)
        source = Source(
            id=source_id,
            candidate_id=candidate,
            type="transcript",
            filename="notes.txt",
            path=None,
            mimetype="text/plain",
            bytes=len(note_bytes),
            checksum=checksum,
        )
        session.add(source)
        note_paragraphs = split_transcript(text_note)
        for index, paragraph in enumerate(note_paragraphs):
            chunk = Chunk(
                id=str(uuid4()),
                source_id=source_id,
                kind="paragraph",
                text=paragraph,
                meta={"order": index},
            )
            session.add(chunk)
        saved_sources.append(SourceInfo(id=source_id, filename="notes.txt"))
        paragraph_counts.append(len(note_paragraphs))

    session.commit()

    return ContextUploadResponse(sources=saved_sources, paragraph_counts=paragraph_counts, saved=True)


@router.get("/sources", response_model=SourceListResponse)
async def list_sources(
    session: SessionDep,
    candidate_id: str = "demo",
    
):
    statement = (
        select(Source, func.count(Chunk.id))
        .join(Chunk, Chunk.source_id == Source.id, isouter=True)
        .where(Source.candidate_id == candidate_id)
        .group_by(Source.id)
        .order_by(Source.created_at.desc())
        .limit(20)
    )
    results = session.execute(statement).all()
    summaries = [
        SourceSummary(
            id=source.id,
            filename=source.filename,
            type=source.type,
            mimetype=source.mimetype,
            bytes=source.bytes,
            created_at=source.created_at,
            chunk_count=int(count or 0),
        )
        for source, count in results
    ]
    return SourceListResponse(sources=summaries)
