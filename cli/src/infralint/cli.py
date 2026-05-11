"""infralint command-line interface."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable

from .config import load_config
from .llm import get_provider
from fnmatch import fnmatch

import click
from rich.console import Console
from rich.table import Table

from . import __version__
from .detection import detect
from .heuristic import Finding, iter_paths, scan_file
from .sarif import to_sarif

_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
_SEVERITY_COLOR = {
    "critical": "bold red",
    "high": "red",
    "medium": "yellow",
    "low": "blue",
    "info": "dim",
}

console = Console()
err_console = Console(stderr=True)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="infralint")
def main() -> None:
    """AI-powered infrastructure-as-code review."""


@main.command()
@click.argument("paths", nargs=-1, required=True, type=click.Path(exists=True, path_type=Path))
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json", "sarif"], case_sensitive=False),
    default="text",
    show_default=True,
    help="Output format.",
)
@click.option(
    "--fail-on",
    type=click.Choice(["critical", "high", "medium", "low", "info", "never"], case_sensitive=False),
    default="never",
    show_default=True,
    help="Exit with code 1 if any finding at or above this severity is present.",
)
@click.option(
    "--llm-provider",
    type=click.Choice(["auto", "claude", "openai", "azure", "ollama", "none"], case_sensitive=False),
    default="auto",
    show_default=True,
    help="Which LLM provider to use to enrich findings (Claude recommended).",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Write output to a file instead of stdout.",
)
def scan(paths: tuple[Path, ...], output_format: str, fail_on: str, llm_provider: str, output: Path | None) -> None:
    """Scan one or more files or directories for infrastructure issues."""
    all_files: list[Path] = []
    for root in paths:
        all_files.extend(iter_paths(root))

    if not all_files:
        err_console.print("[yellow]No supported infrastructure files found.[/yellow]")
        raise SystemExit(0)

    start = Path.cwd()
    if paths:
        start = paths[0].parent if paths[0].is_file() else paths[0]
    cfg = load_config(start)

    if cfg.exclude:
        all_files = [path for path in all_files if not _excluded(path, cfg.exclude)]

    if fail_on == "never" and cfg.fail_on != "never":
        fail_on = cfg.fail_on
    if llm_provider == "auto" and cfg.llm.provider != "auto":
        llm_provider = cfg.llm.provider

    findings: list[Finding] = []
    for path in all_files:
        findings.extend(scan_file(path))

    provider = get_provider(llm_provider, model=cfg.llm.model)
    if provider.name != "none":
        seen = {(finding.rule_id, finding.file, finding.line) for finding in findings}
        for path in all_files:
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for raw in provider.analyze(detect(path), text):
                file_name = str(raw.get("file") or path)
                line = raw.get("line") if isinstance(raw.get("line"), int) else None
                key = (str(raw.get("rule_id") or "INFRALINT-AI-000"), file_name, line)
                if key in seen:
                    continue
                seen.add(key)
                findings.append(Finding(
                    rule_id=key[0],
                    title=str(raw.get("title") or "AI finding"),
                    severity=str(raw.get("severity") or "info").lower(),
                    category=str(raw.get("category") or "security"),
                    description=str(raw.get("description") or raw.get("title") or ""),
                    recommendation=str(raw.get("recommendation") or "Review the configuration and tighten the finding."),
                    file=file_name,
                    line=line,
                ))

    if cfg.disable_rules:
        disabled = set(cfg.disable_rules)
        findings = [finding for finding in findings if finding.rule_id not in disabled]

    findings.sort(key=lambda finding: (_SEVERITY_ORDER.get(finding.severity, 99), finding.file, finding.line or 0))
    rendered = _render(findings, all_files, output_format)

    if output:
        output.write_text(rendered, encoding="utf-8")
        err_console.print(f"[green]Wrote {len(findings)} finding(s) to {output}[/green]")
    elif output_format.lower() != "text":
        click.echo(rendered)

    raise SystemExit(1 if _should_fail(findings, fail_on.lower()) else 0)


def _excluded(path: Path, patterns: list[str]) -> bool:
    normalized = str(path).replace("\\", "/")
    return any(fnmatch(normalized, pattern) for pattern in patterns)


def _render(findings: list[Finding], files: list[Path], output_format: str) -> str:
    fmt = output_format.lower()
    if fmt == "json":
        return json.dumps({
            "summary": _summary(findings, files),
            "findings": [finding.as_dict() for finding in findings],
        }, indent=2)
    if fmt == "sarif":
        return json.dumps(to_sarif(finding.as_dict() for finding in findings), indent=2)

    _render_text(findings, files)
    return ""


def _render_text(findings: list[Finding], files: list[Path]) -> None:
    summary = _summary(findings, files)
    console.print(
        f"\n[bold]infralint[/bold] scanned [cyan]{summary['files_scanned']}[/cyan] file(s) and found [bold]{summary['total']}[/bold] issue(s).\n"
    )

    if not findings:
        console.print("[green]No issues detected.[/green]")
        return

    table = Table(show_header=True, header_style="bold magenta", expand=True)
    table.add_column("Severity", width=10)
    table.add_column("Rule", width=22)
    table.add_column("Title")
    table.add_column("Location", overflow="fold")

    for finding in findings:
        color = _SEVERITY_COLOR.get(finding.severity, "white")
        location = finding.file if not finding.line else f"{finding.file}:{finding.line}"
        table.add_row(
            f"[{color}]{finding.severity.upper()}[/{color}]",
            finding.rule_id,
            finding.title,
            location,
        )

    console.print(table)
    console.print("")
    counts = summary["counts"]
    console.print("  ".join(
        f"[{_SEVERITY_COLOR.get(severity, 'white')}]{severity}={counts.get(severity, 0)}[/{_SEVERITY_COLOR.get(severity, 'white')}]"
        for severity in ("critical", "high", "medium", "low", "info")
    ))


def _summary(findings: Iterable[Finding], files: list[Path]) -> dict[str, object]:
    materialized = list(findings)
    counts: dict[str, int] = {}
    for finding in materialized:
        counts[finding.severity] = counts.get(finding.severity, 0) + 1
    return {
        "files_scanned": len(files),
        "total": len(materialized),
        "counts": counts,
    }


def _should_fail(findings: list[Finding], fail_on: str) -> bool:
    if fail_on == "never":
        return False
    threshold = _SEVERITY_ORDER[fail_on]
    return any(_SEVERITY_ORDER.get(finding.severity, 99) <= threshold for finding in findings)


if __name__ == "__main__":
    main()
