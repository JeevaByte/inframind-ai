import os

import pytest

from infralint.llm import (
    AnthropicProvider,
    NullProvider,
    OllamaProvider,
    OpenAIProvider,
    _safe_parse,
    get_provider,
)

_ENV_VARS = (
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_DEPLOYMENT",
    "OLLAMA_HOST",
)


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    for v in _ENV_VARS:
        monkeypatch.delenv(v, raising=False)


def test_null_provider_returns_empty():
    assert NullProvider().analyze("terraform", "resource x {}") == []


def test_get_provider_none_forced():
    assert isinstance(get_provider("none"), NullProvider)


def test_get_provider_auto_no_keys_returns_null():
    assert isinstance(get_provider("auto"), NullProvider)


def test_get_provider_auto_prefers_claude(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai")
    provider = get_provider("auto")
    assert isinstance(provider, AnthropicProvider)
    assert provider.name == "claude"


def test_get_provider_openai_when_no_claude(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    assert isinstance(get_provider("auto"), OpenAIProvider)


def test_get_provider_forced_ollama_uses_default_host():
    provider = get_provider("ollama")
    assert isinstance(provider, OllamaProvider)
    assert provider.host.startswith("http")


def test_safe_parse_valid_json_array():
    assert _safe_parse('[{"rule_id": "INFRALINT-AI-001"}]') == [{"rule_id": "INFRALINT-AI-001"}]


def test_safe_parse_strips_code_fences():
    assert _safe_parse('```json\n[{"a": 1}]\n```') == [{"a": 1}]


def test_safe_parse_returns_empty_on_garbage():
    assert _safe_parse("not json at all") == []
    assert _safe_parse("") == []


def test_providers_never_raise_without_sdk(monkeypatch):
    """If the SDK isn't importable / network fails, providers must return []."""
    assert AnthropicProvider("fake-key").analyze("dockerfile", "FROM alpine") == []
    assert OpenAIProvider("fake-key").analyze("dockerfile", "FROM alpine") == []
    # Ollama with unreachable host
    assert OllamaProvider(host="http://127.0.0.1:1").analyze("dockerfile", "FROM alpine") == []
