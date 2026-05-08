"""infralint CLI entry point."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List

import click

from .detection import detect
from .findings import Finding
from .scanner import scan_file

# File extensions / names that infralint recognises
_INFRA_SUFFIXES = {".tf", ".tfvars", ".yaml", ".yml", ".json"}
_INFRA_NAMES = {"dockerfile"}


def _collect_files(targets: List[Path]) -> List[Path]:
    """Expand directories and return individual files to scan."""
    collected: List[Path] = []
    for target in targets:
        if target.is_dir():
            for path in sorted(target.rglob("*")):
                if path.is_file() and (
                    path.suffix.lower() in _INFRA_SUFFIXES
                    or path.name.lower() in _INFRA_NAMES
                    or path.name.lower().startswith("dockerfile.")
                ):
                    collected.append(path)
        elif target.is_file():
            collected.append(target)
    return collected


@click.group()
def cli() -> None:
    """infralint — infrastructure-as-code linter."""


@cli.command()
@click.argument("paths", nargs=-1, required=True, type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"], case_sensitive=False),
    default="text",
    show_default=True,
    help="Output format.",
)
@click.option(
    "--severity",
    "-s",
    type=click.Choice(["critical", "high", "medium", "low", "info"], case_sensitive=False),
    default=None,
    help="Minimum severity to report.",
)
@click.option(
    "--llm-provider",
    type=click.Choice(["auto", "openai", "azure", "ollama", "none"], case_sensitive=False),
    default="auto",
    show_default=True,
    help="Which LLM provider to use to enrich findings (auto = detect from env).",
)
def scan(paths: tuple[Path, ...], output: str, severity: str | None, llm_provider: str) -> None:
    """Scan infrastructure files for issues."""
    _SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    min_level = _SEVERITY_ORDER.get((severity or "info").lower(), 4)

    all_files = _collect_files(list(paths))
    if not all_files:
        click.echo("No infrastructure files found.", err=True)
        sys.exit(0)

    findings: List[Finding] = []
    for path in all_files:
        findings.extend(scan_file(path))

    # --- optional LLM enrichment ---
    from .llm import get_provider

    provider = get_provider(llm_provider)
    if provider.name != "none":
        seen = {(f.rule_id, f.file, f.line) for f in findings}
        for path in all_files:
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for raw in provider.analyze(detect(path), text):
                key = (raw.get("rule_id"), raw.get("file") or str(path), raw.get("line"))
                if key in seen:
                    continue
                seen.add(key)
                findings.append(
                    Finding(
                        rule_id=raw.get("rule_id", "INFRALINT-AI-000"),
                        title=raw.get("title", "AI finding"),
                        severity=(raw.get("severity") or "info").lower(),
                        category=raw.get("category", "security"),
                        description=raw.get("description", ""),
                        recommendation=raw.get("recommendation", ""),
                        file=raw.get("file") or str(path),
                        line=raw.get("line"),
                    )
                )

    # --- severity filter ---
    findings = [f for f in findings if _SEVERITY_ORDER.get(f.severity, 4) <= min_level]

    if output.lower() == "json":
        click.echo(json.dumps([f.as_dict() for f in findings], indent=2))
    else:
        if not findings:
            click.echo("No findings.")
        for f in findings:
            line_info = f":{f.line}" if f.line else ""
            click.echo(
                f"[{f.severity.upper()}] {f.rule_id} — {f.title}\n"
                f"  File: {f.file}{line_info}\n"
                f"  {f.description}\n"
                f"  → {f.recommendation}\n"
            )

    has_critical_or_high = any(
        f.severity in ("critical", "high") for f in findings
    )
    sys.exit(1 if has_critical_or_high else 0)
