"""
Multi-LLM Client abstraction.
Supports: Google Gemini (free default), Groq (free tier), OpenAI, Anthropic Claude.
Falls back through providers if one fails.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from config.settings import get_settings

logger = logging.getLogger(__name__)


class LLMClient(ABC):
    """Abstract LLM interface."""

    name: str = "base"

    @abstractmethod
    def chat(self, messages: list[dict], system: str = "") -> str:
        """
        Send a chat completion request.
        messages: list of {"role": "user"|"assistant", "content": str}
        system: system prompt
        Returns: assistant response text
        """
        ...

    def is_available(self) -> bool:
        """Check if this provider is configured and available."""
        return True


class GeminiClient(LLMClient):
    """Google Gemini free tier (15 RPM, 1M tokens/day) — uses httpx REST calls, no SDK needed."""

    name = "gemini"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    def is_available(self) -> bool:
        return bool(self.api_key)

    def chat(self, messages: list[dict], system: str = "") -> str:
        import httpx

        # Convert to Gemini format
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        body: dict = {"contents": contents}
        if system:
            body["system_instruction"] = {"parts": [{"text": system}]}
        body["generationConfig"] = {"temperature": 0.7, "maxOutputTokens": 2000}

        r = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.api_key}",
            headers={"Content-Type": "application/json"},
            json=body,
            timeout=120,
        )
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]


class GroqClient(LLMClient):
    """Groq free tier (Llama 3.3 70B) — uses httpx REST calls, no SDK needed."""

    name = "groq"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    def is_available(self) -> bool:
        return bool(self.api_key)

    def chat(self, messages: list[dict], system: str = "") -> str:
        import httpx

        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        r = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": full_messages,
                "temperature": 0.7,
                "max_tokens": 2000,
            },
            timeout=120,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


class OpenAIClient(LLMClient):
    """OpenAI GPT models — uses httpx REST calls, no SDK needed."""

    name = "openai"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    def is_available(self) -> bool:
        return bool(self.api_key)

    def chat(self, messages: list[dict], system: str = "") -> str:
        import httpx

        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        r = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": full_messages,
                "temperature": 0.7,
                "max_tokens": 2000,
            },
            timeout=120,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


class AnthropicClient(LLMClient):
    """Anthropic Claude models — uses httpx REST calls, no SDK needed."""

    name = "anthropic"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    def is_available(self) -> bool:
        return bool(self.api_key)

    def chat(self, messages: list[dict], system: str = "") -> str:
        import httpx

        r = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 2000,
                "system": system if system else "",
                "messages": messages,
            },
            timeout=120,
        )
        r.raise_for_status()
        return r.json()["content"][0]["text"]


# --- Factory ---

_PROVIDERS = {
    "gemini": GeminiClient,
    "groq": GroqClient,
    "openai": OpenAIClient,
    "anthropic": AnthropicClient,
}


def get_llm_client(provider: str | None = None, api_key: str | None = None) -> LLMClient:
    """
    Get an LLM client instance.
    Falls back through available providers if the requested one isn't available.
    """
    settings = get_settings()
    provider = provider or settings.llm_provider
    api_key = api_key or settings.llm_api_key

    # Try requested provider first
    if provider in _PROVIDERS:
        client = _PROVIDERS[provider](api_key=api_key)
        if client.is_available():
            return client
        logger.warning(f"LLM provider '{provider}' not available, trying fallbacks")

    # Fallback chain
    for name, cls in _PROVIDERS.items():
        if name != provider:
            client = cls(api_key=api_key)
            if client.is_available():
                logger.info(f"Falling back to LLM provider: {name}")
                return client

    raise RuntimeError(
        "No LLM provider available. Please configure an API key in settings. "
        "Supported providers: gemini, groq, openai, anthropic"
    )
