from __future__ import annotations

import asyncio
from typing import Any, Dict

from app.config import Settings


class OpenAIAnalysisClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")

        try:
            from openai import AsyncOpenAI  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - dependency-level failure
            raise RuntimeError(
                "The openai package is required for AI analysis. Install backend requirements first."
            ) from exc

        self._client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=settings.openai_timeout_seconds)

    async def analyze(self, *, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        last_error: Exception | None = None

        for attempt in range(self._settings.openai_max_retries + 1):
            try:
                response = await self._client.chat.completions.create(
                    model=self._settings.openai_model,
                    temperature=0.1,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                content = response.choices[0].message.content or "{}"
                return {"raw_content": content, "model": response.model}
            except Exception as exc:  # pragma: no cover - network/provider dependent
                last_error = exc
                if attempt >= self._settings.openai_max_retries:
                    break
                await asyncio.sleep(0.75 * (attempt + 1))

        raise RuntimeError(f"OpenAI analysis failed: {last_error}") from last_error