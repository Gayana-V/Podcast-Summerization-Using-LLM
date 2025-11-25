"""
Utilities for persisting uploaded audio, transcripts, and summaries.
"""

from pathlib import Path
from typing import Tuple
from uuid import uuid4

from fastapi import UploadFile

from ..config import get_settings

settings = get_settings()


def generate_job_id() -> str:
    return uuid4().hex


def get_job_dir(job_id: str) -> Path:
    job_dir = settings.results_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir


def media_url(job_id: str, filename: str) -> str:
    """Helper to derive API-accessible media URLs."""
    return f"/media/{job_id}/{filename}"


async def save_upload(job_id: str, file: UploadFile) -> Tuple[Path, str]:
    """Persist uploaded file to disk."""
    job_dir = get_job_dir(job_id)
    suffix = Path(file.filename or "audio").suffix or ".mp3"
    dest_path = job_dir / f"source{suffix}"

    with dest_path.open("wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            buffer.write(chunk)

    return dest_path, dest_path.name


def save_text(job_id: str, name: str, content: str) -> Path:
    """Persist textual content to disk."""
    job_dir = get_job_dir(job_id)
    path = job_dir / name
    path.write_text(content, encoding="utf-8")
    return path


def save_binary(job_id: str, name: str, data: bytes) -> Path:
    """Persist binary content."""
    job_dir = get_job_dir(job_id)
    path = job_dir / name
    path.write_bytes(data)
    return path


