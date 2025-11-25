"""
Pydantic models and data structures for PodSummarize.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ProcessingStage(str, Enum):
    UPLOADED = "uploaded"
    TRANSCRIBING = "transcribing"
    DIARIZING = "diarizing"
    SUMMARIZING = "summarizing"
    TTS = "tts"
    COMPLETED = "completed"
    FAILED = "failed"


class SpeakerTurn(BaseModel):
    speaker: str
    start: float
    end: float
    text: str


class TranscriptResult(BaseModel):
    language: Optional[str] = None
    duration: Optional[float] = None
    turns: List[SpeakerTurn] = Field(default_factory=list)


class SummarySection(BaseModel):
    speaker: str
    highlights: List[str]


class SummaryResult(BaseModel):
    overview: str
    per_speaker: List[SummarySection]
    key_points: List[str]


class ProcessingStatus(BaseModel):
    job_id: str
    stage: ProcessingStage
    detail: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    errors: List[str] = Field(default_factory=list)
    assets: Dict[str, str] = Field(default_factory=dict)


class UploadResponse(BaseModel):
    job_id: str
    status: ProcessingStatus


class ProcessRequest(BaseModel):
    job_id: str
    enable_tts: bool = False


class ProcessResponse(BaseModel):
    job_id: str
    status: ProcessingStatus


class ResultsResponse(BaseModel):
    job_id: str
    status: ProcessingStatus
    transcript: Optional[TranscriptResult]
    summary: Optional[SummaryResult]
    audio_url: Optional[str]
    summary_audio_url: Optional[str]


class TTSRequest(BaseModel):
    job_id: str
    text: str
    voice: Optional[str] = None


class TTSResponse(BaseModel):
    job_id: str
    audio_url: str


