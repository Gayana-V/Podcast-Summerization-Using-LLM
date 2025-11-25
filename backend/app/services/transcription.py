"""
Transcription service integrating Whisper (primary) with optional fallbacks.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Dict, List, Tuple
from faster_whisper import WhisperModel


import httpx

from ..config import get_settings
from ..models import SpeakerTurn

settings = get_settings()


class TranscriptionError(RuntimeError):
    """Raised when transcription fails."""


async def transcribe_audio(audio_path: Path) -> Tuple[str, List[SpeakerTurn]]:
    """
    Transcribe the provided audio file and return (language, turns).

    This function first attempts to use OpenAI Whisper. If Whisper fails,
    it will try the configured fallback provider.
    """
    try:
        return await _transcribe_with_whisper(audio_path)
    except Exception as whisper_error:  # noqa: BLE001
        if settings.transcription_provider == "openai":
            raise TranscriptionError(f"Whisper transcription failed: {whisper_error}") from whisper_error

        if settings.transcription_provider == "assemblyai":
            return await _transcribe_with_assembly_ai(audio_path)

        if settings.transcription_provider == "google":
            return await _transcribe_with_google(audio_path)

        raise TranscriptionError("Unsupported transcription provider configured.") from whisper_error


async def _transcribe_with_whisper(audio_path: Path) -> Tuple[str, List[SpeakerTurn]]:
    """
    Local transcription using faster-whisper (no OpenAI API required).
    """
    # Load Whisper model locally (choose "small" or "medium")
    model = WhisperModel("small", device="cpu")  # change to "medium" for higher accuracy if you have resources

    # Transcribe audio file (faster-whisper returns segments and an info object)
    segments, info = model.transcribe(str(audio_path), beam_size=5)

    language = getattr(info, "language", "en")
    turns: List[SpeakerTurn] = []

    for seg in segments:
        turns.append(
            SpeakerTurn(
                speaker="unknown",
                start=seg.start,
                end=seg.end,
                text=seg.text.strip(),
            )
        )

    return language, turns



    # -- Whisper integration end --

    language = payload.get("language", "en")
    segments = payload.get("segments", [])
    if not segments:
        raise TranscriptionError("Whisper returned no segments.")

    turns = [
        SpeakerTurn(
            speaker="unknown",
            start=segment.get("start", 0.0),
            end=segment.get("end", segment.get("start", 0.0)),
            text=segment.get("text", "").strip(),
        )
        for segment in segments
    ]
    return language, turns


async def _transcribe_with_assembly_ai(audio_path: Path) -> Tuple[str, List[SpeakerTurn]]:
    if not settings.assembly_ai_key:
        raise TranscriptionError("AssemblyAI key not configured.")

    # Placeholder for actual AssemblyAI transcription logic.
    await asyncio.sleep(0.1)
    return "en", [
        SpeakerTurn(speaker="unknown", start=0.0, end=2.0, text="Transcription via AssemblyAI not implemented.")
    ]


async def _transcribe_with_google(audio_path: Path) -> Tuple[str, List[SpeakerTurn]]:
    if not settings.google_credentials_json:
        raise TranscriptionError("Google Speech credentials not configured.")

    # Placeholder for actual Google Cloud Speech-To-Text logic.
    await asyncio.sleep(0.1)
    return "en", [SpeakerTurn(speaker="unknown", start=0.0, end=2.0, text="Transcription via Google not implemented.")]


