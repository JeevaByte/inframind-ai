"""LLM provider abstraction for infralint.

Anthropic Claude is the **recommended** provider; OpenAI, Azure OpenAI, and
Ollama are also supported. All providers share a single contract:

    provider.analyze(file_type, content) -> list[dict]

Returned finding dicts use the same keys as `Finding.as_dict()`:
    rule_id, title, severity, category, description, recommendation, file, line

Providers MUST NEVER raise — network/auth/parse failures return an empty list
so a misconfigured key never breaks a scan.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Protocol, runtime_checkable

DEFAULT_CLAUDE_MODEL = "claude-opus-4-5"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_OLLAMA_MODEL = "llama3.1"

_SYSTEM_PROMPT = (
    "You are an expert infrastructure-as-code reviewer. Analyse the supplied "
    "{file_type} file and return ONLY a compact JSON array of findings. Each "
    "finding must be an object with these keys: "
    "rule_id (string starting with INFRALINT-AI-), "
    "title (short), severity (critical|high|medium|low|info), "
    "category (security|reliability|cost|compliance), "
    "description (1-3 sentences, plain English), "
    "recommendation (concrete fix), "
    "line (integer, optional). "
    "Return [] if there are no issues. No prose, no code fences."
)


@runtime_checkable
class LLMProvider(Protocol):
    name: str

    def analyze(self, file_type: str, content: str) -> list[dict[str, Any]]: ...


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_parse(text: str) -> list[dict[str, Any]]:
    """Best-effort extraction of a JSON array from a model response."""
    if not text:
        return []
    # Strip code fences if the model added them.
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if not match:
            return []
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return []
    if isinstance(data, list):
        return [d for d in data if isinstance(d, dict)]
    return []


def _truncate(content: str, max_chars: int = 12_000) -> str:
    if len(content) <= max_chars:
        return content
    return content[:max_chars] + "\n... (truncated by infralint)"


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------

class NullProvider:
    name = "none"

    def analyze(self, file_type: str, content: str) -> list[dict[str, Any]]:
        return []


class AnthropicProvider:
    """Anthropic Claude — the recommended infralint provider."""

    name = "claude"

    def __init__(self, api_key: str, model: str | None = None) -> None:
        self.api_key = api_key
        self.model = model or os.getenv("ANTHROPIC_MODEL") or DEFAULT_CLAUDE_MODEL

    def analyze(self, file_type: str, content: str) -> list[dict[str, Any]]:
        try:
            from anthropic import Anthropic
        except ImportError:
            return []
        try:
            client = Anthropic(api_key=self.api_key)
            response = client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=_SYSTEM_PROMPT.format(file_type=file_type),
                messages=[{"role": "user", "content": _truncate(content)}],
            )
            text = "".join(
                block.text for block in response.content if getattr(block, "type", "") == "text"
            )
            return _safe_parse(text)
        except Exception:
            return []


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str, model: str | None = None) -> None:
        self.api_key = api_key
        self.model = model or os.getenv("OPENAI_MODEL") or DEFAULT_OPENAI_MODEL

    def analyze(self, file_type: str, content: str) -> list[dict[str, Any]]:
        try:
            from openai import OpenAI
        except ImportError:
            return []
        try:
            client = OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT.format(file_type=file_type)
                                                  + ' Wrap the array in {"findings": [...]}.'},
                    {"role": "user", "content": _truncate(content)},
                ],
            )
            text = response.choices[0].message.content or ""
            try:
                obj = json.loads(text)
            except json.JSONDecodeError:
                return _safe_parse(text)
            if isinstance(obj, dict) and isinstance(obj.get("findings"), list):
                return [d for d in obj["findings"] if isinstance(d, dict)]
            return []
        except Exception:
            return []


class AzureOpenAIProvider:
    name = "azure"

    def __init__(
        self,
        api_key: str,
        endpoint: str,
        deployment: str,
        api_version: str = "2024-08-01-preview",
    ) -> None:
        self.api_key = api_key
        self.endpoint = endpoint
        self.deployment = deployment
        self.api_version = api_version

    def analyze(self, file_type: str, content: str) -> list[dict[str, Any]]:
        try:
            from openai import AzureOpenAI
        except ImportError:
            return []
        try:
            client = AzureOpenAI(
                api_key=self.api_key,
                azure_endpoint=self.endpoint,
                api_version=self.api_version,
            )
            response = client.chat.completions.create(
                model=self.deployment,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT.format(file_type=file_type)
                                                  + ' Wrap the array in {"findings": [...]}.'},
                    {"role": "user", "content": _truncate(content)},
                ],
            )
            text = response.choices[0].message.content or ""
            try:
                obj = json.loads(text)
            except json.JSONDecodeError:
                return _safe_parse(text)
            if isinstance(obj, dict) and isinstance(obj.get("findings"), list):
                return [d for d in obj["findings"] if isinstance(d, dict)]
            return []
        except Exception:
            return []


class OllamaProvider:
    name = "ollama"

    def __init__(self, host: str | None = None, model: str | None = None) -> None:
        self.host = (host or os.getenv("OLLAMA_HOST") or "http://localhost:11434").rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL") or DEFAULT_OLLAMA_MODEL

    def analyze(self, file_type: str, content: str) -> list[dict[str, Any]]:
        try:
            import httpx
        except ImportError:
            return []
        try:
            response = httpx.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "system": _SYSTEM_PROMPT.format(file_type=file_type),
                    "prompt": _truncate(content),
                    "stream": False,
                    "format": "json",
                },
                timeout=60.0,
            )
            response.raise_for_status()
            return _safe_parse(response.json().get("response", ""))
        except Exception:
            return []


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------

def get_provider(forced: str | None = None, model: str | None = None) -> LLMProvider:
    """Return a provider based on env vars or a forced choice.

    Selection order when forced in {None, "auto"}:
        1. Anthropic Claude  (ANTHROPIC_API_KEY)
        2. OpenAI            (OPENAI_API_KEY)
        3. Azure OpenAI      (AZURE_OPENAI_API_KEY + AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_DEPLOYMENT)
        4. Ollama            (OLLAMA_HOST set explicitly)
        5. NullProvider
    """
    choice = (forced or "auto").lower()

    if choice == "none":
        return NullProvider()

    if choice in ("auto", "claude", "anthropic") and os.getenv("ANTHROPIC_API_KEY"):
        return AnthropicProvider(os.environ["ANTHROPIC_API_KEY"], model=model)

    if choice in ("auto", "openai") and os.getenv("OPENAI_API_KEY"):
        return OpenAIProvider(os.environ["OPENAI_API_KEY"], model=model)

    if choice in ("auto", "azure"):
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        if api_key and endpoint and deployment:
            return AzureOpenAIProvider(api_key, endpoint, deployment)

    if choice == "ollama" or (choice == "auto" and os.getenv("OLLAMA_HOST")):
        return OllamaProvider(model=model)

    return NullProvider()
