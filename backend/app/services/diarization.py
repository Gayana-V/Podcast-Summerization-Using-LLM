"""
Diarization service leveraging the Hoard framework.
"""

from __future__ import annotations

import asyncio
from typing import List

try:
    # Hoard's Python package is assumed to be available.
    from hoard import HoardDiarizer  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    HoardDiarizer = None  # type: ignore

from ..models import SpeakerTurn


class DiarizationError(RuntimeError):
    """Raised when diarization fails."""


async def diarize(transcript_turns: List[SpeakerTurn], audio_path: str) -> List[SpeakerTurn]:
    """
    Perform diarization using Hoard to reassign speaker labels for each turn.

    Hoard expects an audio path and an initial transcript with timestamps.
    """
    if HoardDiarizer is None:
        # Provide a graceful fallback for environments without Hoard.
        await asyncio.sleep(0.1)
        # Assign pseudo speakers in round-robin fashion.
        speakers = ["Speaker 1", "Speaker 2"]
        return [
            SpeakerTurn(
                speaker=speakers[index % len(speakers)],
                start=turn.start,
                end=turn.end,
                text=turn.text,
            )
            for index, turn in enumerate(transcript_turns)
        ]

    # -- Hoard integration start --
    # Initialize Hoard with default configuration. In production you can tune
    # embedding model, clustering strategy, or VAD parameters via config files.
    diarizer = HoardDiarizer()  # type: ignore[call-arg]

    diarized_segments = diarizer.run(  # type: ignore[attr-defined]
        audio_path=audio_path,
        transcript=[
            {
                "start": turn.start,
                "end": turn.end,
                "text": turn.text,
            }
            for turn in transcript_turns
        ],
    )
    # -- Hoard integration end --

    if not diarized_segments:
        raise DiarizationError("Hoard returned no diarization segments.")

    return [
        SpeakerTurn(
            speaker=segment.get("speaker", f"Speaker {index + 1}"),
            start=float(segment.get("start", 0.0)),
            end=float(segment.get("end", 0.0)),
            text=segment.get("text", ""),
        )
        for index, segment in enumerate(diarized_segments)
    ]


