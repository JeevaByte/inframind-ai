import os

from infralint.llm import get_provider, NullProvider


def test_get_provider_none(monkeypatch):
    for v in ("OPENAI_API_KEY", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "OLLAMA_HOST"):
        monkeypatch.delenv(v, raising=False)
    assert isinstance(get_provider("none"), NullProvider)
    assert isinstance(get_provider("auto"), NullProvider)


def test_null_provider_returns_empty():
    assert NullProvider().analyze("terraform", "resource x {}") == []
