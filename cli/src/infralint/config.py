"""Load .infralint.yaml configuration from the nearest ancestor directory."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

CONFIG_FILENAME = ".infralint.yaml"


@dataclass
class LLMConfig:
    # auto | claude | openai | azure | ollama | none. Claude is recommended.
    provider: str = "auto"
    model: str | None = None


@dataclass
class Config:
    exclude: list[str] = field(default_factory=list)
    disable_rules: list[str] = field(default_factory=list)
    fail_on: str = "never"
    llm: LLMConfig = field(default_factory=LLMConfig)
    source: Path | None = None


def find_config_file(start: Path) -> Path | None:
    """Walk upward from start looking for .infralint.yaml."""
    start = start.resolve()
    for parent in [start, *start.parents]:
        candidate = parent / CONFIG_FILENAME
        if candidate.is_file():
            return candidate
    return None


def load_config(start: Path) -> Config:
    path = find_config_file(start)
    if not path:
        return Config()
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return Config()
    llm_raw = data.get("llm") or {}
    return Config(
        exclude=list(data.get("exclude") or []),
        disable_rules=list(data.get("disable_rules") or []),
        fail_on=str(data.get("fail_on") or "never"),
        llm=LLMConfig(
            provider=str(llm_raw.get("provider", "auto")),
            model=llm_raw.get("model"),
        ),
        source=path,
    )
