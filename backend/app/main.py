"""
FastAPI application entry point for PodSummarize.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .config import Settings, get_settings
from .models import (
    ProcessRequest,
    ProcessResponse,
    ResultsResponse,
    TTSRequest,
    TTSResponse,
    UploadResponse,
)
from .services import pipeline
from .services.storage import generate_job_id, save_upload

app = FastAPI(title="PodSummarize Backend")


def configure_cors(app: FastAPI, settings: Settings) -> None:
    origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
    if getattr(app.state, "cors_configured", False):
        return
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins if origins else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.cors_configured = True


configure_cors(app, get_settings())


def get_audio_file_path(job_id: str, filename: str) -> Path:
    return pipeline.get_job_dir(job_id) / filename


@app.post("/upload", response_model=UploadResponse)
async def upload_podcast(
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    podcast_url: Optional[str] = None,
) -> UploadResponse:
    """
    Upload a podcast audio file or provide a public URL for download.

    For URLs we queue a download task; for files we store immediately.
    """
    if not file and not podcast_url:
        raise HTTPException(status_code=400, detail="Provide either an audio file or a podcast URL.")

    job_id = generate_job_id()
    status = pipeline.pipeline_state.create_status(job_id)

    if file:
        audio_path, name = await save_upload(job_id, file)
        pipeline.register_audio_asset(job_id, str(audio_path))
    else:
        background_tasks.add_task(_download_podcast_audio, job_id, podcast_url)

    return UploadResponse(job_id=job_id, status=status)


async def _download_podcast_audio(job_id: str, podcast_url: str) -> None:
    """Download audio from given URL and store for processing."""
    import httpx

    try:
        if not podcast_url:
            raise ValueError("Podcast URL missing.")
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.get(podcast_url)
            response.raise_for_status()
            audio_bytes = response.content

        path = pipeline.get_job_dir(job_id) / "source.mp3"
        path.write_bytes(audio_bytes)
        pipeline.register_audio_asset(job_id, str(path))
    except Exception as exc:  # noqa: BLE001
        pipeline.pipeline_state.add_error(job_id, f"Download failed: {exc}")


@app.post("/process", response_model=ProcessResponse)
async def start_processing(request: ProcessRequest, background_tasks: BackgroundTasks) -> ProcessResponse:
    """Trigger transcription, diarization, summarization, and optional TTS."""
    try:
        job_dir = pipeline.get_job_dir(request.job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc

    audio_candidates = list(job_dir.glob("source.*"))
    if not audio_candidates:
        raise HTTPException(status_code=400, detail="Audio source not available for processing.")

    audio_path = audio_candidates[0]
    background_tasks.add_task(pipeline.launch_background, request.job_id, str(audio_path), request.enable_tts)
    status = pipeline.ensure_job(request.job_id)
    return ProcessResponse(job_id=request.job_id, status=status)


@app.get("/results/{job_id}", response_model=ResultsResponse)
async def fetch_results(job_id: str) -> ResultsResponse:
    """Retrieve processing status, transcript, and summary data."""
    try:
        return pipeline.pipeline_state.results(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc


@app.post("/tts", response_model=TTSResponse)
async def generate_summary_audio(request: TTSRequest) -> TTSResponse:
    """Generate TTS for provided summary text."""
    try:
        pipeline.ensure_job(request.job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc

    summary_audio_path = await pipeline.tts.synthesize_tts(request)
    relative_path = str(summary_audio_path)
    pipeline.pipeline_state.store_summary_audio(request.job_id, relative_path)

    return TTSResponse(job_id=request.job_id, audio_url=relative_path)


@app.get("/media/{job_id}/{filename}")
async def serve_media(job_id: str, filename: str) -> FileResponse:
    """Serve stored media assets."""
    path = get_audio_file_path(job_id, filename)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Media file not found.")
    media_type = "audio/mpeg" if path.suffix == ".mp3" else "application/octet-stream"
    return FileResponse(path, media_type=media_type)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}


