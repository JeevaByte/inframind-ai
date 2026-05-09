"""LLM provider abstraction. Auto-detects from environment."""
from __future__ import annotations

import os
from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    name: str

    def analyze(self, file_type: str, content: str) -> list[dict]: ...


class NullProvider:
    name = "none"

    def analyze(self, file_type: str, content: str) -> list[dict]:
        return []


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model

    def analyze(self, file_type: str, content: str) -> list[dict]:
        # Lazy import so openai is optional at runtime
        try:
            from openai import OpenAI
        except ImportError:
            return []

        # Minimal call — returns [] on any failure (never raises)
        try:
            client = OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an infrastructure security expert. "
                            "Analyze the provided infrastructure-as-code content and return a JSON object "
                            "with a single key 'findings' containing an array of finding objects. "
                            "Each finding must have keys: rule_id (string starting with 'INFRALINT-AI-'), "
                            "title, severity (critical/high/medium/low/info), category "
                            "(security/reliability/cost/compliance), description, recommendation, "
                            "file (empty string if unknown), line (integer or null). "
                            "Return an empty findings array if there are no issues."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"File type: {file_type}\n\n{content}",
                    },
                ],
            )
            import json

            raw = json.loads(response.choices[0].message.content or "{}")
            return raw.get("findings", [])
        except Exception:
            return []


class AzureOpenAIProvider:
    name = "azure"

    def __init__(self) -> None:
        self.api_key = os.environ.get("AZURE_OPENAI_API_KEY", "")
        self.endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
        self.deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")

    def analyze(self, file_type: str, content: str) -> list[dict]:
        # Lazy import so openai is optional at runtime
        try:
            from openai import AzureOpenAI
        except ImportError:
            return []

        try:
            api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-01")
            client = AzureOpenAI(
                api_key=self.api_key,
                azure_endpoint=self.endpoint,
                api_version=api_version,
            )
            response = client.chat.completions.create(
                model=self.deployment,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an infrastructure security expert. "
                            "Analyze the provided infrastructure-as-code content and return a JSON object "
                            "with a single key 'findings' containing an array of finding objects. "
                            "Each finding must have keys: rule_id (string starting with 'INFRALINT-AI-'), "
                            "title, severity (critical/high/medium/low/info), category "
                            "(security/reliability/cost/compliance), description, recommendation, "
                            "file (empty string if unknown), line (integer or null). "
                            "Return an empty findings array if there are no issues."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"File type: {file_type}\n\n{content}",
                    },
                ],
            )
            import json

            raw = json.loads(response.choices[0].message.content or "{}")
            return raw.get("findings", [])
        except Exception:
            return []


class OllamaProvider:
    name = "ollama"

    def __init__(self) -> None:
        self.host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self.model = os.environ.get("OLLAMA_MODEL", "llama3")

    def analyze(self, file_type: str, content: str) -> list[dict]:
        # Lazy import so httpx is optional at runtime
        try:
            import httpx
        except ImportError:
            return []

        prompt = (
            "You are an infrastructure security expert. "
            "Analyze the provided infrastructure-as-code content and return ONLY a JSON object "
            "with a single key 'findings' containing an array of finding objects. "
            "Each finding must have keys: rule_id (string starting with 'INFRALINT-AI-'), "
            "title, severity (critical/high/medium/low/info), category "
            "(security/reliability/cost/compliance), description, recommendation, "
            "file (empty string if unknown), line (integer or null). "
            "Return an empty findings array if there are no issues.\n\n"
            f"File type: {file_type}\n\n{content}"
        )

        try:
            resp = httpx.post(
                f"{self.host}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False, "format": "json"},
                timeout=120,
            )
            resp.raise_for_status()
            import json

            raw = json.loads(resp.json().get("response", "{}"))
            return raw.get("findings", [])
        except Exception:
            return []


def get_provider(forced: str | None = None) -> LLMProvider:
    """Return a provider based on env vars or a forced choice.

    forced: one of None | "auto" | "openai" | "azure" | "ollama" | "none"
    """
    choice = (forced or "auto").lower()
    if choice == "none":
        return NullProvider()
    if choice in ("auto", "openai") and os.getenv("OPENAI_API_KEY"):
        return OpenAIProvider(os.environ["OPENAI_API_KEY"])
    if (
        choice in ("auto", "azure")
        and os.getenv("AZURE_OPENAI_API_KEY")
        and os.getenv("AZURE_OPENAI_ENDPOINT")
    ):
        return AzureOpenAIProvider()
    if choice in ("auto", "ollama") and (os.getenv("OLLAMA_HOST") or choice == "ollama"):
        return OllamaProvider()
    return NullProvider()
