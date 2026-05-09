"""
LLM client with vLLM primary endpoint (AMD MI300X) and public API fallback.
Uses OpenAI-compatible API for both endpoints.
"""

import json
import logging
import time
import re
from typing import AsyncGenerator
from openai import AsyncOpenAI, APIConnectionError, APITimeoutError

from backend.config import Settings

log = logging.getLogger(__name__)


class LLMClient:
    """
    Wraps the OpenAI-compatible API.
    Primary: vLLM on AMD MI300X (api_key="EMPTY").
    Fallback: Together.ai or any public Qwen API.
    """

    def __init__(self, settings: Settings):
        self._model = settings.vllm_model
        self._fallback_model = settings.fallback_model
        self._max_tokens = settings.llm_max_tokens
        self._temperature = settings.llm_temperature
        self._total_tokens = 0
        self._total_time = 0.0

        self._primary = AsyncOpenAI(
            base_url=settings.vllm_base_url,
            api_key="EMPTY",
            timeout=settings.llm_timeout,
            max_retries=1,
        )

        self._fallback: AsyncOpenAI | None = None
        if settings.fallback_api_key:
            self._fallback = AsyncOpenAI(
                base_url=settings.fallback_base_url,
                api_key=settings.fallback_api_key,
                timeout=settings.llm_timeout,
                max_retries=2,
            )
        else:
            log.warning("No FALLBACK_API_KEY set — LLM will fail if vLLM endpoint is unreachable")

    async def chat(
        self,
        messages: list[dict],
        max_tokens: int | None = None,
        temperature: float | None = None,
        system: str | None = None,
    ) -> str:
        """Send a chat request. Returns assistant message content string."""
        if system:
            messages = [{"role": "system", "content": system}] + list(messages)

        mt = max_tokens or self._max_tokens
        temp = temperature or self._temperature

        t0 = time.time()
        try:
            resp = await self._primary.chat.completions.create(
                model=self._model,
                messages=messages,
                max_tokens=mt,
                temperature=temp,
            )
            content = resp.choices[0].message.content or ""
            elapsed = time.time() - t0
            tokens = resp.usage.completion_tokens if resp.usage else 0
            self._total_tokens += tokens
            self._total_time += elapsed
            log.info(f"vLLM: {tokens} tokens in {elapsed:.1f}s ({tokens/elapsed:.0f} tok/s)")
            return content

        except (APIConnectionError, APITimeoutError, Exception) as primary_err:
            log.warning(f"Primary vLLM endpoint failed ({primary_err}), trying fallback...")
            if not self._fallback:
                raise RuntimeError("vLLM endpoint unreachable and no fallback API key configured") from primary_err
            try:
                resp = await self._fallback.chat.completions.create(
                    model=self._fallback_model,
                    messages=messages,
                    max_tokens=mt,
                    temperature=temp,
                )
                content = resp.choices[0].message.content or ""
                elapsed = time.time() - t0
                tokens = resp.usage.completion_tokens if resp.usage else 0
                self._total_tokens += tokens
                self._total_time += elapsed
                log.info(f"Fallback API: {tokens} tokens in {elapsed:.1f}s")
                return content
            except Exception as fallback_err:
                raise RuntimeError(f"Both LLM endpoints failed. Primary: {primary_err}. Fallback: {fallback_err}")

    async def chat_stream(
        self,
        messages: list[dict],
        max_tokens: int | None = None,
        system: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completions, yielding token chunks."""
        if system:
            messages = [{"role": "system", "content": system}] + list(messages)

        try:
            stream = await self._primary.chat.completions.create(
                model=self._model,
                messages=messages,
                max_tokens=max_tokens or self._max_tokens,
                temperature=self._temperature,
                stream=True,
            )
            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except Exception:
            if self._fallback:
                stream = await self._fallback.chat.completions.create(
                    model=self._fallback_model,
                    messages=messages,
                    max_tokens=max_tokens or self._max_tokens,
                    stream=True,
                )
                async for chunk in stream:
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield delta

    @property
    def total_tokens(self) -> int:
        return self._total_tokens

    @property
    def avg_tokens_per_second(self) -> float:
        if self._total_time > 0:
            return self._total_tokens / self._total_time
        return 0.0


def extract_json(raw: str) -> dict | list:
    """Extract JSON from LLM response, handling markdown fences."""
    # Strip markdown fences
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("```").strip()

    # Try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object/array within the text
    for pattern in [r'\{.*\}', r'\[.*\]']:
        match = re.search(pattern, cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                continue

    raise ValueError(f"Could not extract valid JSON from LLM response: {raw[:200]}")
