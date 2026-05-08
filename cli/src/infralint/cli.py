"""infralint CLI — scan infrastructure files for security and best-practice issues."""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from typing import List, Optional

from .config import load_config

SUPPORTED_EXTENSIONS = {
    ".tf", ".yaml", ".yml", ".json", ".dockerfile",
}


@dataclass
class Finding:
    rule_id: str
    severity: str
    message: str
    file: Path
    line: Optional[int] = None


def _collect_files(paths: List[Path]) -> List[Path]:
    """Recursively collect infrastructure files from the given paths."""
    files: List[Path] = []
    for p in paths:
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            for ext in SUPPORTED_EXTENSIONS:
                files.extend(p.rglob(f"*{ext}"))
            # Also collect Dockerfile variants by name
            files.extend(p.rglob("Dockerfile*"))
    # Deduplicate while preserving order
    seen: set = set()
    result: List[Path] = []
    for f in files:
        key = f.resolve()
        if key not in seen:
            seen.add(key)
            result.append(f)
    return result


def _run_heuristics(files: List[Path]) -> List[Finding]:
    """Run built-in heuristic checks and return findings."""
    findings: List[Finding] = []
    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        # Basic placeholder checks — extended by heuristic.py
        if "privileged: true" in text:
            findings.append(Finding(
                rule_id="INFRALINT-K8S-001",
                severity="high",
                message="Container running in privileged mode",
                file=f,
            ))
        if "allowPrivilegeEscalation: true" in text:
            findings.append(Finding(
                rule_id="INFRALINT-K8S-002",
                severity="medium",
                message="allowPrivilegeEscalation is enabled",
                file=f,
            ))
    return findings


_SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}


def _meets_threshold(severity: str, threshold: str) -> bool:
    return _SEVERITY_RANK.get(severity, 0) >= _SEVERITY_RANK.get(threshold, 0)


def scan(
    paths: List[Path],
    fail_on: str = "never",
    llm_provider: str = "auto",
    output_format: str = "text",
) -> int:
    """Scan *paths* for findings and return an exit code."""
    all_files = _collect_files(paths)

    # --- Load .infralint.yaml config ---
    cfg = load_config(paths[0] if paths else Path.cwd())

    if cfg.exclude:
        def _excluded(p: Path) -> bool:
            s = str(p).replace("\\", "/")
            return any(fnmatch(s, pat) for pat in cfg.exclude)
        all_files = [p for p in all_files if not _excluded(p)]

    # CLI flag overrides config; config overrides default "never"
    if fail_on == "never" and cfg.fail_on != "never":
        fail_on = cfg.fail_on
    if llm_provider == "auto" and cfg.llm.provider != "auto":
        llm_provider = cfg.llm.provider

    # Run heuristics
    findings = _run_heuristics(all_files)

    # LLM enrichment placeholder (populated by Agent 03)
    # findings = _enrich_with_llm(findings, provider=llm_provider, model=cfg.llm.model)

    # Filter disabled rules
    if cfg.disable_rules:
        disabled = set(cfg.disable_rules)
        findings = [f for f in findings if f.rule_id not in disabled]

    # Output
    if output_format == "text":
        for finding in findings:
            loc = f":{finding.line}" if finding.line else ""
            print(f"[{finding.severity.upper()}] {finding.rule_id} {finding.file}{loc} — {finding.message}")
        if not findings:
            print("No findings.")

    # Exit code
    if fail_on == "never":
        return 0
    for finding in findings:
        if _meets_threshold(finding.severity, fail_on):
            return 1
    return 0


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        prog="infralint",
        description="Scan infrastructure files for security issues.",
    )
    parser.add_argument("paths", nargs="*", default=["."], help="Paths to scan")
    parser.add_argument("--fail-on", default="never",
                        choices=["never", "info", "low", "medium", "high", "critical"],
                        help="Exit 1 when findings at or above this severity exist")
    parser.add_argument("--llm-provider", default="auto",
                        choices=["auto", "openai", "azure", "ollama", "none"],
                        help="LLM provider for enrichment")
    parser.add_argument("--format", default="text", choices=["text", "json"],
                        dest="output_format", help="Output format")
    args = parser.parse_args()

    resolved = [Path(p) for p in args.paths]
    sys.exit(scan(resolved, fail_on=args.fail_on,
                  llm_provider=args.llm_provider,
                  output_format=args.output_format))


if __name__ == "__main__":
    main()
