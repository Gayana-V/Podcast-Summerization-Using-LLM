# """
# Processing pipeline orchestrating transcription, diarization, summarization, and TTS.
# """

# from __future__ import annotations

# import asyncio
# from datetime import datetime
# from typing import Dict, Optional

# from pathlib import Path

# from ..models import (
#     ProcessingStage,
#     ProcessingStatus,
#     ResultsResponse,
#     SummaryResult,
#     TranscriptResult,
#     TTSRequest,
# )
# from . import diarization, llm, transcription, tts
# from .storage import get_job_dir as storage_get_job_dir, media_url, save_text


# class PipelineState:
#     """In-memory job tracker."""

#     def __init__(self) -> None:
#         self._jobs: Dict[str, ProcessingStatus] = {}
#         self._transcripts: Dict[str, TranscriptResult] = {}
#         self._summaries: Dict[str, SummaryResult] = {}
#         self._summary_audio: Dict[str, str] = {}

#     def create_status(self, job_id: str) -> ProcessingStatus:
#         now = datetime.utcnow()
#         status = ProcessingStatus(
#             job_id=job_id,
#             stage=ProcessingStage.UPLOADED,
#             created_at=now,
#             updated_at=now,
#         )
#         self._jobs[job_id] = status
#         return status

#     def update_stage(self, job_id: str, stage: ProcessingStage, detail: Optional[str] = None) -> None:
#         status = self._jobs[job_id]
#         status.stage = stage
#         status.detail = detail
#         status.updated_at = datetime.utcnow()

#     def add_error(self, job_id: str, message: str) -> None:
#         status = self._jobs[job_id]
#         status.errors.append(message)
#         status.stage = ProcessingStage.FAILED
#         status.updated_at = datetime.utcnow()

#     def store_transcript(self, job_id: str, transcript: TranscriptResult) -> None:
#         self._transcripts[job_id] = transcript

#     def store_summary(self, job_id: str, summary: SummaryResult) -> None:
#         self._summaries[job_id] = summary

#     def store_summary_audio(self, job_id: str, path: str) -> None:
#         self._summary_audio[job_id] = path

#     def get(self, job_id: str) -> ProcessingStatus:
#         return self._jobs[job_id]

#     def results(self, job_id: str) -> ResultsResponse:
#         status = self._jobs[job_id]
#         transcript = self._transcripts.get(job_id)
#         summary = self._summaries.get(job_id)
#         audio_url = status.assets.get("source_audio")
#         summary_audio_url = self._summary_audio.get(job_id)
#         return ResultsResponse(
#             job_id=job_id,
#             status=status,
#             transcript=transcript,
#             summary=summary,
#             audio_url=audio_url,
#             summary_audio_url=summary_audio_url,
#         )


# pipeline_state = PipelineState()


# async def process_job(job_id: str, audio_path: str, enable_tts: bool = False) -> ProcessingStatus:
#     """Execute the sequential processing pipeline."""
#     try:
#         pipeline_state.update_stage(job_id, ProcessingStage.TRANSCRIBING, "Running transcription")
#         language, turns = await transcription.transcribe_audio(Path(audio_path))
#         transcript = TranscriptResult(language=language, turns=turns)
#         pipeline_state.store_transcript(job_id, transcript)
#         transcript_path = save_text(job_id, "transcript.json", transcript.json(indent=2))
#         pipeline_state.get(job_id).assets["transcript"] = media_url(job_id, transcript_path.name)

#         pipeline_state.update_stage(job_id, ProcessingStage.DIARIZING, "Applying Hoard diarization")
#         diarized_turns = await diarization.diarize(transcript.turns, audio_path)
#         transcript.turns = diarized_turns
#         diarized_path = save_text(job_id, "diarized.json", transcript.json(indent=2))
#         pipeline_state.get(job_id).assets["diarized_transcript"] = media_url(job_id, diarized_path.name)

#         pipeline_state.update_stage(job_id, ProcessingStage.SUMMARIZING, "Generating LLM summary")
#         summary = await llm.summarize(transcript.turns)
#         pipeline_state.store_summary(job_id, summary)
#         summary_path = save_text(job_id, "summary.json", summary.json(indent=2))
#         pipeline_state.get(job_id).assets["summary"] = media_url(job_id, summary_path.name)

#         if enable_tts:
#             pipeline_state.update_stage(job_id, ProcessingStage.TTS, "Synthesizing summary audio")
#             tts_request = TTSRequest(job_id=job_id, text=summary.overview)
#             summary_audio_path = await tts.synthesize_tts(tts_request)
#             pipeline_state.store_summary_audio(job_id, media_url(job_id, summary_audio_path.name))

#         pipeline_state.update_stage(job_id, ProcessingStage.COMPLETED, "Processing complete")

#     except Exception as exc:  # noqa: BLE001
#         pipeline_state.add_error(job_id, str(exc))

#     return pipeline_state.get(job_id)


# async def launch_background(job_id: str, audio_path: str, enable_tts: bool = False) -> None:
#     """Spawn background task for processing."""
#     asyncio.create_task(process_job(job_id, audio_path, enable_tts))


# def register_audio_asset(job_id: str, asset_path: str) -> None:
#     """Store path to uploaded audio."""
#     status = pipeline_state.get(job_id)
#     filename = Path(asset_path).name
#     status.assets["source_audio"] = media_url(job_id, filename)


# def ensure_job(job_id: str) -> ProcessingStatus:
#     """Return existing job status."""
#     return pipeline_state.get(job_id)


# def get_job_dir(job_id: str) -> Path:
#     """Expose storage job directory helper."""
#     return storage_get_job_dir(job_id)

"""
Processing pipeline orchestrating transcription, diarization, summarization, and TTS.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Dict, Optional

from pathlib import Path

from ..models import (
    ProcessingStage,
    ProcessingStatus,
    ResultsResponse,
    SummaryResult,
    TranscriptResult,
    TTSRequest,
)
from . import diarization, llm, transcription, tts
from .storage import get_job_dir as storage_get_job_dir, media_url, save_text


class PipelineState:
    """In-memory job tracker."""

    def __init__(self) -> None:
        self._jobs: Dict[str, ProcessingStatus] = {}
        self._transcripts: Dict[str, TranscriptResult] = {}
        self._summaries: Dict[str, SummaryResult] = {}
        self._summary_audio: Dict[str, str] = {}

    def create_status(self, job_id: str) -> ProcessingStatus:
        now = datetime.utcnow()
        status = ProcessingStatus(
            job_id=job_id,
            stage=ProcessingStage.UPLOADED,
            created_at=now,
            updated_at=now,
        )
        self._jobs[job_id] = status
        return status

    def update_stage(self, job_id: str, stage: ProcessingStage, detail: Optional[str] = None) -> None:
        status = self._jobs[job_id]
        status.stage = stage
        status.detail = detail
        status.updated_at = datetime.utcnow()

    def add_error(self, job_id: str, message: str) -> None:
        status = self._jobs[job_id]
        status.errors.append(message)
        status.stage = ProcessingStage.FAILED
        status.updated_at = datetime.utcnow()

    def store_transcript(self, job_id: str, transcript: TranscriptResult) -> None:
        self._transcripts[job_id] = transcript

    def store_summary(self, job_id: str, summary: SummaryResult) -> None:
        self._summaries[job_id] = summary

    def store_summary_audio(self, job_id: str, path: str) -> None:
        self._summary_audio[job_id] = path

    def get(self, job_id: str) -> ProcessingStatus:
        return self._jobs[job_id]

    def results(self, job_id: str) -> ResultsResponse:
        status = self._jobs[job_id]
        transcript = self._transcripts.get(job_id)
        summary = self._summaries.get(job_id)
        audio_url = status.assets.get("source_audio")
        summary_audio_url = self._summary_audio.get(job_id)
        return ResultsResponse(
            job_id=job_id,
            status=status,
            transcript=transcript,
            summary=summary,
            audio_url=audio_url,
            summary_audio_url=summary_audio_url,
        )


pipeline_state = PipelineState()


async def process_job(job_id: str, audio_path: str, enable_tts: bool = False) -> ProcessingStatus:
    """Execute the sequential processing pipeline."""
    try:
        pipeline_state.update_stage(job_id, ProcessingStage.TRANSCRIBING, "Running transcription")
        language, turns = await transcription.transcribe_audio(Path(audio_path))
        transcript = TranscriptResult(language=language, turns=turns)
        pipeline_state.store_transcript(job_id, transcript)
        transcript_path = save_text(job_id, "transcript.json", transcript.json(indent=2))
        pipeline_state.get(job_id).assets["transcript"] = media_url(job_id, transcript_path.name)

        pipeline_state.update_stage(job_id, ProcessingStage.DIARIZING, "Applying Hoard diarization")
        diarized_turns = await diarization.diarize(transcript.turns, audio_path)
        transcript.turns = diarized_turns
        diarized_path = save_text(job_id, "diarized.json", transcript.json(indent=2))
        pipeline_state.get(job_id).assets["diarized_transcript"] = media_url(job_id, diarized_path.name)

        pipeline_state.update_stage(job_id, ProcessingStage.SUMMARIZING, "Generating LLM summary")
        summary = await llm.summarize(transcript.turns)
        pipeline_state.store_summary(job_id, summary)
        summary_path = save_text(job_id, "summary.json", summary.json(indent=2))
        pipeline_state.get(job_id).assets["summary"] = media_url(job_id, summary_path.name)

        if enable_tts:
            pipeline_state.update_stage(job_id, ProcessingStage.TTS, "Synthesizing summary audio")
            tts_request = TTSRequest(job_id=job_id, text=summary.overview)
            summary_audio_path = await tts.synthesize_tts(tts_request)
            pipeline_state.store_summary_audio(job_id, media_url(job_id, summary_audio_path.name))

        pipeline_state.update_stage(job_id, ProcessingStage.COMPLETED, "Processing complete")

    except Exception as exc:  # noqa: BLE001
        pipeline_state.add_error(job_id, str(exc))

    return pipeline_state.get(job_id)


async def launch_background(job_id: str, audio_path: str, enable_tts: bool = False) -> None:
    """Spawn background task for processing."""
    asyncio.create_task(process_job(job_id, audio_path, enable_tts))


def register_audio_asset(job_id: str, asset_path: str) -> None:
    """Store path to uploaded audio."""
    status = pipeline_state.get(job_id)
    filename = Path(asset_path).name
    status.assets["source_audio"] = media_url(job_id, filename)


def ensure_job(job_id: str) -> ProcessingStatus:
    """Return existing job status."""
    return pipeline_state.get(job_id)


def get_job_dir(job_id: str) -> Path:
    """Expose storage job directory helper."""
    return storage_get_job_dir(job_id)


