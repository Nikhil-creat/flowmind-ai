"""
Provider-agnostic AI layer. Tries the configured primary provider first;
if it isn't configured or the call fails after retries, automatically
falls back to the other provider. This keeps document Q&A and AI workflow
nodes working even if one vendor has an outage or a missing key.
"""
from __future__ import annotations

from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings

settings = get_settings()


def _claude_available() -> bool:
    return bool(settings.ANTHROPIC_API_KEY)


def _gemini_available() -> bool:
    return bool(settings.GOOGLE_API_KEY)


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4), reraise=True)
def _call_claude(prompt: str, max_tokens: int) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=settings.AI_MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4), reraise=True)
def _call_gemini(prompt: str, max_tokens: int) -> str:
    import google.generativeai as genai

    genai.configure(api_key=settings.GOOGLE_API_KEY)
    model = genai.GenerativeModel(settings.GEMINI_MODEL)
    response = model.generate_content(
        prompt, generation_config={"max_output_tokens": max_tokens}
    )
    return response.text or ""


def generate(prompt: str, max_tokens: int = 600) -> dict[str, str]:
    """Returns {"text": ..., "provider": "claude"|"gemini"|"none"}."""
    providers_in_order = (
        ["claude", "gemini"] if settings.AI_PROVIDER == "claude" else ["gemini", "claude"]
    )

    for provider in providers_in_order:
        if provider == "claude" and _claude_available():
            try:
                return {"text": _call_claude(prompt, max_tokens), "provider": "claude"}
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"Claude call failed, trying fallback: {exc}")
        elif provider == "gemini" and _gemini_available():
            try:
                return {"text": _call_gemini(prompt, max_tokens), "provider": "gemini"}
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"Gemini call failed, trying fallback: {exc}")

    return {"text": "", "provider": "none"}
