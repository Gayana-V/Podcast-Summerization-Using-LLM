# """
# Text-to-speech synthesis integration.
# """

# from __future__ import annotations

# import asyncio
# from pathlib import Path

# import httpx

# from ..config import get_settings
# from ..models import TTSRequest
# from .storage import save_binary

# settings = get_settings()


# class TTSError(RuntimeError):
#     """Raised when TTS fails."""


# async def synthesize_tts(request: TTSRequest) -> Path:
#     """Generate an audio rendition of the summary text."""
#     provider = settings.tts_provider.lower()
#     if provider == "azure":
#         return await _synthesize_azure(request)
#     if provider == "google":
#         return await _synthesize_google(request)
#     if provider == "coqui":
#         return await _synthesize_coqui(request)
#     raise TTSError("TTS provider not configured or unsupported.")


# async def _synthesize_azure(request: TTSRequest) -> Path:
#     if not settings.azure_speech_key or not settings.azure_speech_region:
#         raise TTSError("Azure Speech credentials are missing.")

#     voice = request.voice or settings.tts_voice
#     ssml = f"""
# <speak version="1.0" xml:lang="en-US">
#   <voice name="{voice}">
#     {request.text}
#   </voice>
# </speak>
# """

#     headers = {
#         "Ocp-Apim-Subscription-Key": settings.azure_speech_key,
#         "Content-Type": "application/ssml+xml",
#         "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3",
#         "User-Agent": "PodSummarize",
#     }

#     url = f"https://{settings.azure_speech_region}.tts.speech.microsoft.com/cognitiveservices/v1"

#     # -- TTS synthesis integration start --
#     async with httpx.AsyncClient(timeout=120) as client:
#         response = await client.post(url, headers=headers, content=ssml.encode("utf-8"))
#         response.raise_for_status()
#         audio_bytes = response.content
#     # -- TTS synthesis integration end --

#     return save_binary(request.job_id, "summary.mp3", audio_bytes)


# async def _synthesize_google(request: TTSRequest) -> Path:
#     await asyncio.sleep(0.1)
#     dummy_audio = b""
#     return save_binary(request.job_id, "summary.mp3", dummy_audio)


# async def _synthesize_coqui(request: TTSRequest) -> Path:
#     await asyncio.sleep(0.1)
#     dummy_audio = b""
#     return save_binary(request.job_id, "summary.mp3", dummy_audio)

"""
Text-to-speech synthesis integration.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import httpx

from ..config import get_settings
from ..models import TTSRequest
from .storage import save_binary

settings = get_settings()


class TTSError(RuntimeError):
    """Raised when TTS fails."""


async def synthesize_tts(request: TTSRequest) -> Path:
    """Generate an audio rendition of the summary text."""
    provider = settings.tts_provider.lower()

    if provider == "azure":
        return await _synthesize_azure(request)
    if provider == "google":
        return await _synthesize_google(request)
    if provider == "coqui":
        return await _synthesize_coqui(request)
    if provider == "elevenlabs":
        return await _synthesize_elevenlabs(request)

    raise TTSError("TTS provider not configured or unsupported.")


# ------------------------------
# Azure TTS (Existing)
# ------------------------------
async def _synthesize_azure(request: TTSRequest) -> Path:
    if not settings.azure_speech_key or not settings.azure_speech_region:
        raise TTSError("Azure Speech credentials are missing.")

    voice = request.voice or settings.tts_voice
    ssml = f"""
<speak version="1.0" xml:lang="en-US">
  <voice name="{voice}">
    {request.text}
  </voice>
</speak>
"""

    headers = {
        "Ocp-Apim-Subscription-Key": settings.azure_speech_key,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3",
        "User-Agent": "PodSummarize",
    }

    url = f"https://{settings.azure_speech_region}.tts.speech.microsoft.com/cognitiveservices/v1"

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(url, headers=headers, content=ssml.encode("utf-8"))
        response.raise_for_status()
        audio_bytes = response.content

    return save_binary(request.job_id, "summary.mp3", audio_bytes)


# ------------------------------
# Google TTS (Dummy)
# ------------------------------
async def _synthesize_google(request: TTSRequest) -> Path:
    await asyncio.sleep(0.1)
    dummy_audio = b""
    return save_binary(request.job_id, "summary.mp3", dummy_audio)


# ------------------------------
# Coqui TTS (Dummy)
# ------------------------------
async def _synthesize_coqui(request: TTSRequest) -> Path:
    await asyncio.sleep(0.1)
    dummy_audio = b""
    return save_binary(request.job_id, "summary.mp3", dummy_audio)


# ------------------------------
# ElevenLabs TTS (UPDATED)
# ------------------------------
async def _synthesize_elevenlabs(request: TTSRequest) -> Path:
    """ElevenLabs text-to-speech integration."""
    if not settings.elevenlabs_api_key:
        raise TTSError("ElevenLabs API key missing.")

    voice_id = request.voice or settings.elevenlabs_voice or "EXAVITQu4vr4xnSDxMaL"

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "xi-api-key": settings.elevenlabs_api_key,
        "Content-Type": "application/json",
    }

    # Updated to new ElevenLabs free-tier-compatible model
    payload = {
        "text": request.text,
        "model_id": "eleven_turbo_v2",
    }

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            raise TTSError(f"ElevenLabs TTS failed: {response.text}")

        audio_bytes = response.content

    return save_binary(request.job_id, "summary.mp3", audio_bytes)
