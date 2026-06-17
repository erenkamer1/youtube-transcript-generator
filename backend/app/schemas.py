from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class SegmentSchema(BaseModel):
    start: float
    end: float
    text: str


class TranscribeRequest(BaseModel):
    url: str


class TranscribeResult(BaseModel):
    id: int
    url: str
    title: str
    duration: float | None
    language: str | None
    segments: list[SegmentSchema]
    full_text: str


class TranslateRequest(BaseModel):
    transcript_id: int | None = None
    text: str | None = None
    target_language: str = Field(default="Turkish", min_length=2)
    model: str | None = None
    tone: Literal["formal", "casual"] = "formal"


class GeneratePromptRequest(BaseModel):
    transcript_id: int | None = None
    text: str | None = None
    template: Literal[
        "detailed_notes",
        "bullet_summary",
        "rules_tips",
        "study_guide",
        "quiz",
    ] = "detailed_notes"
    language: str = "Turkish"


class GeneratePromptResponse(BaseModel):
    template: str
    prompt: str


class SummarizeRequest(BaseModel):
    transcript_id: int | None = None
    text: str | None = None
    model: str | None = None
    language: str = "Turkish"


class HistoryItem(BaseModel):
    id: int
    url: str
    title: str
    duration: float | None
    language: str | None
    created_at: datetime
    segment_count: int


class OllamaModel(BaseModel):
    name: str
    size: int | None = None


class ProgressEvent(BaseModel):
    stage: str
    message: str
    progress: float | None = None
