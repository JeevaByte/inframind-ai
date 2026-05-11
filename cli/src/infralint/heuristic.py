"""Heuristic, no-LLM scanner used as the default fallback."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .detection import (
    CLOUDFORMATION,
    DOCKERFILE,
    GITHUB_ACTIONS,
    KUBERNETES,
    TERRAFORM,
    detect,
)


@dataclass
class Finding:
    rule_id: str
    title: str
    severity: str
    category: str
    description: str
    recommendation: str
    file: str
    line: int | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "rule_id": self.rule_id,
            "title": self.title,
            "severity": self.severity,
            "category": self.category,
            "description": self.description,
            "recommendation": self.recommendation,
            "file": self.file,
            "line": self.line,
        }


_PATTERN_RULES: list[tuple[str, str, str, str, str, str, re.Pattern[str]]] = [
    (
        "INFRALINT-SEC-001",
        "Hardcoded secret or credential",
        "critical",
        "security",
        "Secrets in source control are a top cause of breaches and cannot be rotated easily.",
        "Move the value to a secret manager and reference it via environment or workload identity.",
        re.compile(r"(password|secret|token|api[_-]?key|access[_-]?key)\s*[:=]\s*[\"']?[A-Za-z0-9/+=_\-]{8,}", re.IGNORECASE),
    ),
    (
        "INFRALINT-SEC-002",
        "World-open network access (0.0.0.0/0)",
        "high",
        "security",
        "Allowing 0.0.0.0/0 exposes the resource to the entire internet.",
        "Restrict CIDR ranges to known ingress sources or front the resource with a managed gateway.",
        re.compile(r"0\.0\.0\.0/0"),
    ),
    (
        "INFRALINT-SEC-003",
        "Public object-storage ACL",
        "high",
        "security",
        "Public-read or public-read-write ACLs expose object data to anyone on the internet.",
        "Use explicit principals and private storage policies instead of public ACLs.",
        re.compile(r"public-read(-write)?", re.IGNORECASE),
    ),
    (
        "INFRALINT-SEC-004",
        "IAM wildcard action",
        "high",
        "security",
        "Wildcard actions violate least privilege and are hard to audit safely.",
        "Enumerate only the concrete actions required by the workload.",
        re.compile(r"Action\s*[:=]\s*[\"']\*[\"']|actions\s*=\s*\[[^\]]*\*", re.IGNORECASE),
    ),
]

_DOCKERFILE_LATEST = re.compile(r"^FROM\s+[^\s:]+:latest\b", re.IGNORECASE | re.MULTILINE)
_DOCKERFILE_ROOT = re.compile(r"^USER\s+root\b", re.IGNORECASE | re.MULTILINE)
_DOCKERFILE_ADD_URL = re.compile(r"^ADD\s+https?://", re.IGNORECASE | re.MULTILINE)

_K8S_PRIVILEGED = re.compile(r"privileged:\s*true", re.IGNORECASE)
_K8S_HOST_NETWORK = re.compile(r"hostNetwork:\s*true", re.IGNORECASE)
_K8S_NO_RESOURCES = re.compile(r"resources:\s*\{\s*\}")

_TF_S3_BUCKET = re.compile(r'resource\s+"aws_s3_bucket"', re.IGNORECASE)
_TF_HAS_SSE = re.compile(r"server_side_encryption", re.IGNORECASE)


def _scan_dockerfile(text: str, file: str) -> list[Finding]:
    findings: list[Finding] = []
    if _DOCKERFILE_LATEST.search(text):
        findings.append(Finding(
            rule_id="INFRALINT-DOCKER-001",
            title="Image uses :latest tag",
            severity="medium",
            category="reliability",
            description="Pinning to :latest produces non-reproducible builds and surprise upgrades.",
            recommendation="Pin to an immutable digest or a specific version tag.",
            file=file,
        ))
    if _DOCKERFILE_ROOT.search(text):
        findings.append(Finding(
            rule_id="INFRALINT-DOCKER-002",
            title="Container runs as root",
            severity="high",
            category="security",
            description="Running as root inside the container increases the blast radius of runtime compromise.",
            recommendation="Add a non-root USER and adjust file ownership in the image.",
            file=file,
        ))
    if _DOCKERFILE_ADD_URL.search(text):
        findings.append(Finding(
            rule_id="INFRALINT-DOCKER-003",
            title="ADD with remote URL",
            severity="medium",
            category="security",
            description="Downloading remote content during build can change without warning and bypass integrity checks.",
            recommendation="Use curl or wget with checksum verification in a RUN step instead.",
            file=file,
        ))
    return findings


def _scan_kubernetes(text: str, file: str) -> list[Finding]:
    findings: list[Finding] = []
    if _K8S_PRIVILEGED.search(text):
        findings.append(Finding(
            rule_id="INFRALINT-K8S-001",
            title="Privileged container",
            severity="critical",
            category="security",
            description="privileged: true effectively grants the container broad access to the host kernel.",
            recommendation="Drop the privileged flag and add only the specific capabilities required.",
            file=file,
        ))
    if _K8S_HOST_NETWORK.search(text):
        findings.append(Finding(
            rule_id="INFRALINT-K8S-002",
            title="Pod uses host network",
            severity="high",
            category="security",
            description="hostNetwork: true bypasses pod network isolation.",
            recommendation="Remove hostNetwork unless absolutely required.",
            file=file,
        ))
    if _K8S_NO_RESOURCES.search(text):
        findings.append(Finding(
            rule_id="INFRALINT-K8S-003",
            title="Container has no resource requests/limits",
            severity="medium",
            category="reliability",
            description="Without requests and limits, workloads can starve the node or be evicted unexpectedly.",
            recommendation="Set CPU and memory requests and limits appropriate for the workload.",
            file=file,
        ))
    return findings


def _scan_terraform(text: str, file: str) -> list[Finding]:
    findings: list[Finding] = []
    if _TF_S3_BUCKET.search(text) and not _TF_HAS_SSE.search(text):
        findings.append(Finding(
            rule_id="INFRALINT-TF-001",
            title="S3 bucket without explicit server-side encryption",
            severity="high",
            category="security",
            description="Object storage should define explicit server-side encryption rather than relying on ambient defaults.",
            recommendation="Add a server-side encryption configuration using AES256 or a KMS key.",
            file=file,
        ))
    return findings


def _scan_generic(text: str, file: str) -> list[Finding]:
    findings: list[Finding] = []
    for rule_id, title, severity, category, description, recommendation, pattern in _PATTERN_RULES:
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            findings.append(Finding(
                rule_id=rule_id,
                title=title,
                severity=severity,
                category=category,
                description=description,
                recommendation=recommendation,
                file=file,
                line=line,
            ))
    return findings


def scan_file(path: Path) -> list[Finding]:
    """Scan a single file with the heuristic engine."""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    file_type = detect(path)
    findings = _scan_generic(text, str(path))

    if file_type == DOCKERFILE:
        findings.extend(_scan_dockerfile(text, str(path)))
    elif file_type == KUBERNETES:
        findings.extend(_scan_kubernetes(text, str(path)))
    elif file_type == TERRAFORM:
        findings.extend(_scan_terraform(text, str(path)))
    elif file_type in (CLOUDFORMATION, GITHUB_ACTIONS):
        pass

    return findings


def iter_paths(root: Path) -> Iterable[Path]:
    """Yield candidate files under root that look scannable."""
    if root.is_file():
        yield root
        return

    ignored = {".git", "node_modules", ".venv", "__pycache__", "dist", "build"}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in ignored for part in path.parts):
            continue
        if detect(path) != "unknown":
            yield path