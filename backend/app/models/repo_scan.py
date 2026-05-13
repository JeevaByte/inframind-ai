from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.models.common import AnalysisStatus, Finding, Severity


class RepoScannerName(str, Enum):
    CHECKOV = "checkov"
    PROWLER = "prowler"
    TRIVY = "trivy"
    GITLEAKS = "gitleaks"
    SEMGREP = "semgrep"
    TFSEC = "tfsec"


class RepoSummary(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0
    total: int = 0


class RepoScannerResult(BaseModel):
    scanner: RepoScannerName
    status: AnalysisStatus
    findings: List[Finding] = Field(default_factory=list)
    summary: RepoSummary = Field(default_factory=RepoSummary)
    command: List[str] = Field(default_factory=list)
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RepoScanRequest(BaseModel):
    repository: str
    github_token: Optional[str] = None
    ref: Optional[str] = None
    scanners: List[RepoScannerName] = Field(
        default_factory=lambda: [
            RepoScannerName.CHECKOV,
            RepoScannerName.TRIVY,
            RepoScannerName.GITLEAKS,
            RepoScannerName.SEMGREP,
        ]
    )


class RepoScanResult(BaseModel):
    scan_id: UUID = Field(default_factory=uuid4)
    repository: str
    ref: Optional[str] = None
    status: AnalysisStatus = AnalysisStatus.PENDING
    findings: List[Finding] = Field(default_factory=list)
    summary: RepoSummary = Field(default_factory=RepoSummary)
    scanners: List[RepoScannerResult] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RepoScanListResponse(BaseModel):
    scans: List[RepoScanResult] = Field(default_factory=list)
    total: int = 0


def summarize_findings(findings: List[Finding]) -> RepoSummary:
    summary = RepoSummary(total=len(findings))
    for finding in findings:
        if finding.severity == Severity.CRITICAL:
            summary.critical += 1
        elif finding.severity == Severity.HIGH:
            summary.high += 1
        elif finding.severity == Severity.MEDIUM:
            summary.medium += 1
        elif finding.severity == Severity.LOW:
            summary.low += 1
        else:
            summary.info += 1
    return summary
