"""Heuristic scanner for infrastructure-as-code files."""
from __future__ import annotations

import re
from pathlib import Path
from typing import List

from .detection import detect
from .findings import Finding

_SECRET_RE = re.compile(
    r"(password|secret|token|api[_-]?key|access[_-]?key)\s*[:=]\s*[\"']?[^\s\"']+",
    re.IGNORECASE,
)
_PUBLIC_RE = re.compile(r"0\.0\.0\.0/0|public-read|public-read-write", re.IGNORECASE)
_WILDCARD_IAM_RE = re.compile(
    r'Action\s*[:=]\s*["\'\s]*\*["\'\s]|actions\s*=\s*\[[^\]]*\*',
    re.IGNORECASE,
)
_LATEST_TAG_RE = re.compile(r":latest\b", re.IGNORECASE)
_NO_USER_RE = re.compile(r"^USER\s+", re.MULTILINE)


def scan_file(path: Path) -> List[Finding]:
    """Run heuristic checks on *path* and return a list of Finding objects."""
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    file_type = detect(path)
    findings: List[Finding] = []
    file_str = str(path)

    # --- secrets (all file types) ---
    for match in _SECRET_RE.finditer(content):
        line = content[: match.start()].count("\n") + 1
        findings.append(
            Finding(
                rule_id="INFRALINT-SEC-001",
                title="Potential hardcoded secret",
                severity="critical",
                category="security",
                description="The file contains a value that looks like a hardcoded credential or token.",
                recommendation="Replace inline credentials with secret references or environment injection.",
                file=file_str,
                line=line,
            )
        )
        break  # one finding per file for secrets

    # --- public exposure ---
    if _PUBLIC_RE.search(content):
        findings.append(
            Finding(
                rule_id="INFRALINT-SEC-002",
                title="Public exposure pattern found",
                severity="high",
                category="security",
                description="The configuration includes markers associated with public network or storage exposure.",
                recommendation="Review whether the resource must be internet-facing and add compensating controls.",
                file=file_str,
                line=None,
            )
        )

    # --- wildcard IAM ---
    if file_type == "terraform" and _WILDCARD_IAM_RE.search(content):
        findings.append(
            Finding(
                rule_id="INFRALINT-SEC-003",
                title="Wildcard IAM permissions detected",
                severity="critical",
                category="security",
                description="IAM configuration contains wildcard permissions that violate least privilege.",
                recommendation="Scope actions and resources to the smallest set required by the workload.",
                file=file_str,
                line=None,
            )
        )

    # --- dockerfile: no USER ---
    if file_type == "dockerfile" and not _NO_USER_RE.search(content):
        findings.append(
            Finding(
                rule_id="INFRALINT-SEC-004",
                title="Docker image runs as default root user",
                severity="high",
                category="security",
                description="The Dockerfile does not switch to a non-root USER.",
                recommendation="Add a dedicated non-root user before the final runtime stage.",
                file=file_str,
                line=None,
            )
        )

    # --- unpinned :latest ---
    if file_type == "dockerfile" and _LATEST_TAG_RE.search(content):
        findings.append(
            Finding(
                rule_id="INFRALINT-COMP-001",
                title="Unpinned container image tag",
                severity="medium",
                category="compliance",
                description="The Dockerfile references a latest-tagged base image.",
                recommendation="Pin the image to a specific version or digest for reproducibility.",
                file=file_str,
                line=None,
            )
        )

    return findings
