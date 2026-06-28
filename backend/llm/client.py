"""
LLM client with multi-provider fallback chain: vLLM (primary) → Groq → Gemini → OpenRouter.
Uses OpenAI-compatible API for all endpoints.
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
    Multi-provider LLM client with cascading fallback.
    Primary: vLLM (configurable)
    Fallback chain: Groq → Gemini → OpenRouter
    """

    def __init__(self, settings: Settings):
        self._model = settings.vllm_model
        self._max_tokens = settings.llm_max_tokens
        self._temperature = settings.llm_temperature
        self._total_tokens = 0
        self._total_time = 0.0

        # Primary provider
        self._primary = AsyncOpenAI(
            base_url=settings.vllm_base_url,
            api_key="EMPTY",
            timeout=settings.llm_timeout,
            max_retries=1,
        )
        self._primary_model = settings.vllm_model

        # Build fallback chain dynamically (only include providers with API keys)
        self._fallbacks: list[tuple[AsyncOpenAI, str, str]] = []
        
        # Groq
        if settings.groq_api_key:
            self._fallbacks.append((
                AsyncOpenAI(
                    base_url=settings.groq_base_url,
                    api_key=settings.groq_api_key,
                    timeout=settings.llm_timeout,
                    max_retries=1,
                ),
                settings.groq_model,
                "Groq"
            ))
        # Gemini (note: uses openai-compatible endpoint)
        if settings.gemini_api_key:
            self._fallbacks.append((
                AsyncOpenAI(
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai",
                    api_key=settings.gemini_api_key,
                    timeout=settings.llm_timeout,
                    max_retries=1,
                ),
                settings.gemini_model,
                "Gemini"
            ))
        # OpenRouter
        if settings.openrouter_api_key:
            self._fallbacks.append((
                AsyncOpenAI(
                    base_url=settings.openrouter_base_url,
                    api_key=settings.openrouter_api_key,
                    timeout=settings.llm_timeout,
                    max_retries=1,
                ),
                settings.openrouter_model,
                "OpenRouter"
            ))
        
        # Legacy fallback for backwards compatibility
        if settings.fallback_api_key and not self._fallbacks:
            self._fallbacks.append((
                AsyncOpenAI(
                    base_url=settings.fallback_base_url,
                    api_key=settings.fallback_api_key,
                    timeout=settings.llm_timeout,
                    max_retries=1,
                ),
                settings.fallback_model,
                "LegacyFallback"
            ))

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
        last_error: Exception | None = None

        # Try primary
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
        except (APIConnectionError, APITimeoutError, Exception) as err:
            last_error = err
            log.warning(f"Primary LLM endpoint failed ({err})")

        # Try fallback chain
        for client, model, provider_name in self._fallbacks:
            try:
                resp = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=mt,
                    temperature=temp,
                )
                content = resp.choices[0].message.content or ""
                elapsed = time.time() - t0
                tokens = resp.usage.completion_tokens if resp.usage else 0
                self._total_tokens += tokens
                self._total_time += elapsed
                log.info(f"{provider_name}: {tokens} tokens in {elapsed:.1f}s")
                return content
            except Exception as fallback_err:
                last_error = fallback_err
                log.warning(f"{provider_name} fallback failed: {fallback_err}")
                continue

        raise RuntimeError(f"All LLM endpoints failed. Last error: {last_error}") from last_error

    async def chat_stream(
        self,
        messages: list[dict],
        max_tokens: int | None = None,
        system: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completions, yielding token chunks."""
        if system:
            messages = [{"role": "system", "content": system}] + list(messages)

        # Try primary first
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
            return
        except Exception:
            pass

        # Fallback chain with streaming
        for client, model, provider_name in self._fallbacks:
            try:
                stream = await client.chat.completions.create(
                    model=model,
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
                return
            except Exception:
                continue

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
