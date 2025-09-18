from __future__ import annotations

from typing import List, Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from services import DummyGptService

router = APIRouter()
service = DummyGptService()


class HealthResponse(BaseModel):
    ok: bool = True


class AnalyzeJDRequest(BaseModel):
    jd_text: str = Field(..., min_length=1)


class SkillItem(BaseModel):
    name: str
    importance: str

    model_config = ConfigDict(extra="allow")


class JDSection(BaseModel):
    title: str
    bullets: List[str]

    model_config = ConfigDict(extra="allow")


class AnalyzeJDResponse(BaseModel):
    summary: str
    key_requirements: List[str]
    skills: List[SkillItem]
    sections: List[JDSection]

    model_config = ConfigDict(extra="allow")


class JDJson(BaseModel):
    title: str
    location: str | None = None
    responsibilities: List[str] | None = None

    model_config = ConfigDict(extra="allow")


class CandidateChunk(BaseModel):
    id: str
    heading: str
    content: str

    model_config = ConfigDict(extra="allow")


class AssessRequest(BaseModel):
    jd_json: JDJson
    candidate_chunks: List[CandidateChunk]


class FitAssessmentResponse(BaseModel):
    score: int
    verdict: str
    strengths: List[str]
    gaps: List[str]
    next_steps: List[str]

    model_config = ConfigDict(extra="allow")


class RewriteCVRequest(BaseModel):
    project_id: str = Field(..., min_length=1)
    mode: Literal["conservative", "bold"]


class RewriteSection(BaseModel):
    heading: str
    content: str

    model_config = ConfigDict(extra="allow")


class RewriteCVResponse(BaseModel):
    project_id: str
    mode: Literal["conservative", "bold"]
    sections: List[RewriteSection]

    model_config = ConfigDict(extra="allow")


class QARequest(BaseModel):
    jd_json: JDJson
    candidate_chunks: List[CandidateChunk]


class QAItem(BaseModel):
    question: str
    answer: str

    model_config = ConfigDict(extra="allow")


class QAResponse(BaseModel):
    questions: List[QAItem]

    model_config = ConfigDict(extra="allow")


@router.get("/healthz", response_model=HealthResponse)
async def healthcheck() -> HealthResponse:
    return HealthResponse(ok=True)


@router.post("/analyze_jd", response_model=AnalyzeJDResponse)
async def analyze_jd(payload: AnalyzeJDRequest) -> AnalyzeJDResponse:
    mock = service.analyze_job_description(payload.jd_text)
    return AnalyzeJDResponse.model_validate(mock)


@router.post("/assess", response_model=FitAssessmentResponse)
async def assess_candidate(payload: AssessRequest) -> FitAssessmentResponse:
    mock = service.assess_candidate_fit(payload.jd_json.model_dump(), [chunk.model_dump() for chunk in payload.candidate_chunks])
    return FitAssessmentResponse.model_validate(mock)


@router.post("/rewrite_cv", response_model=RewriteCVResponse)
async def rewrite_cv(payload: RewriteCVRequest) -> RewriteCVResponse:
    mock = service.rewrite_cv(payload.project_id, payload.mode)
    return RewriteCVResponse.model_validate(mock)


@router.post("/qa", response_model=QAResponse)
async def generate_qa(payload: QARequest) -> QAResponse:
    mock = service.generate_qa(payload.jd_json.model_dump(), [chunk.model_dump() for chunk in payload.candidate_chunks])
    return QAResponse.model_validate(mock)
