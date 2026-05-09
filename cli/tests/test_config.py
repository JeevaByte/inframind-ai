from pathlib import Path

from infralint.config import load_config


def test_no_config_returns_defaults(tmp_path: Path):
    cfg = load_config(tmp_path)
    assert cfg.exclude == []
    assert cfg.disable_rules == []
    assert cfg.fail_on == "never"
    assert cfg.llm.provider == "auto"


def test_loads_yaml(tmp_path: Path):
    (tmp_path / ".infralint.yaml").write_text(
        "exclude:\n"
        "  - 'samples/**'\n"
        "disable_rules:\n"
        "  - INFRALINT-DOCKER-001\n"
        "fail_on: high\n"
        "llm:\n"
        "  provider: ollama\n"
    )
    cfg = load_config(tmp_path)
    assert cfg.exclude == ["samples/**"]
    assert "INFRALINT-DOCKER-001" in cfg.disable_rules
    assert cfg.fail_on == "high"
    assert cfg.llm.provider == "ollama"
