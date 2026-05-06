from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable

from app.models.common import FindingCategory, Severity


_SEVERITY_PENALTIES: Dict[Severity, int] = {
    Severity.CRITICAL: 28,
    Severity.HIGH: 18,
    Severity.MEDIUM: 10,
    Severity.LOW: 4,
    Severity.INFO: 1,
}


@dataclass
class ScoringResult:
    overall_score: float
    security_score: float
    reliability_score: float
    cost_optimization_score: float
    compliance_score: float
    deployment_readiness: str


def _score_bucket(findings: Iterable[tuple[FindingCategory, Severity]], category: FindingCategory | None = None) -> float:
    relevant = [severity for finding_category, severity in findings if category is None or finding_category == category]
    if not relevant:
      return 100.0

    penalty = sum(_SEVERITY_PENALTIES[severity] for severity in relevant)
    return round(max(0.0, 100.0 - penalty), 1)


def score_findings(findings: Iterable[tuple[FindingCategory, Severity]]) -> ScoringResult:
    collected = list(findings)
    overall = _score_bucket(collected)
    security = _score_bucket(collected, FindingCategory.SECURITY)
    reliability = _score_bucket(collected, FindingCategory.RELIABILITY)
    cost = _score_bucket(collected, FindingCategory.COST)
    compliance = _score_bucket(collected, FindingCategory.COMPLIANCE)

    severities = [severity for _, severity in collected]
    if Severity.CRITICAL in severities:
        readiness = "Not ready"
    elif Severity.HIGH in severities:
        readiness = "Needs remediation"
    elif Severity.MEDIUM in severities:
        readiness = "Review before deploy"
    else:
        readiness = "Ready with minor follow-up"

    return ScoringResult(
        overall_score=overall,
        security_score=security,
        reliability_score=reliability,
        cost_optimization_score=cost,
        compliance_score=compliance,
        deployment_readiness=readiness,
    )