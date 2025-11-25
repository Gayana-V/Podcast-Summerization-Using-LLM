"""
LLM-based summarization service.
"""

from __future__ import annotations

import asyncio
from typing import List

import httpx

from ..config import get_settings
from ..models import SpeakerTurn, SummaryResult, SummarySection

settings = get_settings()


class SummarizationError(RuntimeError):
    """Raised when summarization fails."""


SUMMARY_PROMPT = """Summarize this transcript, giving per-speaker highlights and overall episode summary.

Return JSON with keys: overview (string), key_points (list of strings), per_speaker (list of {speaker, highlights[]}).
"""


async def summarize(transcript_turns: List[SpeakerTurn]) -> SummaryResult:
    """Call configured LLM provider to generate a structured summary."""
    if not transcript_turns:
        raise SummarizationError("Transcript is empty.")

    content = "\n".join(
        f"[{turn.start:.2f}-{turn.end:.2f}] {turn.speaker}: {turn.text}" for turn in transcript_turns
    )

    provider = settings.llm_provider.lower()
    if provider == "openai":
        response = await _call_openai(content)
    elif provider == "deepseek":
        response = await _call_deepseek(content)
    elif provider == "gemini":
        response = await _call_gemini(content)
    else:
        response = await _call_custom(content)

    overview = response.get("overview") or "Summary unavailable."
    key_points = response.get("key_points") or []
    per_speaker_data = response.get("per_speaker") or []

    per_speaker = [
        SummarySection(
            speaker=item.get("speaker", "Unknown"),
            highlights=item.get("highlights") or [],
        )
        for item in per_speaker_data
    ]

    return SummaryResult(overview=overview, key_points=key_points, per_speaker=per_speaker)


async def _call_openai(content: str) -> dict:
    if not settings.llm_api_key and not settings.openai_api_key:
        raise SummarizationError("OpenAI API key not configured.")
    api_key = settings.llm_api_key or settings.openai_api_key

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.llm_model,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": "You are an expert podcast summarizer."},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": SUMMARY_PROMPT,
                    },
                    {
                        "type": "text",
                        "text": content,
                    },
                ],
            },
        ],
    }

    # -- LLM invocation start --
    async with httpx.AsyncClient(timeout=120) as client:
        result = await client.post(
            "https://api.openai.com/v1/responses",
            headers=headers,
            json=payload,
        )
        result.raise_for_status()
        data = result.json()
    # -- LLM invocation end --

    message = data.get("output", {}) or data.get("choices", [{}])[0].get("message", {}).get("content")
    if isinstance(message, dict):
        return message
    if isinstance(message, str):
        import json

        return json.loads(message)
    raise SummarizationError("Unexpected OpenAI response format.")


async def _call_deepseek(content: str) -> dict:
    if not settings.llm_api_key:
        raise SummarizationError("DeepSeek API key not configured.")

    await asyncio.sleep(0.1)
    return {
        "overview": "DeepSeek summary placeholder.",
        "key_points": ["Integration with DeepSeek not implemented."],
        "per_speaker": [{"speaker": "Speaker 1", "highlights": ["Placeholder"]}],
    }


async def _call_custom(content: str) -> dict:
    await asyncio.sleep(0.1)
    return {
        "overview": "Custom provider not configured.",
        "key_points": ["Set LLM_PROVIDER to openai, gemini, or deepseek."],
        "per_speaker": [{"speaker": "Speaker 1", "highlights": ["Transcript content truncated."]}],
    }


async def _call_gemini(content: str) -> dict:
    api_key = settings.gemini_api_key or settings.llm_api_key
    if not api_key:
        raise SummarizationError("Gemini API key not configured.")

    endpoint = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.llm_model or 'gemini-1.5-flash-latest'}:generateContent"
    )
    params = {"key": api_key}
    prompt_text = f"{SUMMARY_PROMPT}\n\nTranscript:\n{content}"

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt_text,
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
        },
    }

    # -- Gemini invocation start --
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(endpoint, params=params, json=payload)
        response.raise_for_status()
        data = response.json()
    # -- Gemini invocation end --

    try:
        candidates = data.get("candidates") or []
        first = candidates[0]
        parts = first["content"]["parts"]
        text = parts[0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise SummarizationError("Unexpected Gemini response format.") from exc

    import json

    return json.loads(text)


