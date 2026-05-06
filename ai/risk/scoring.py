"""
Risk scoring engine for InfraMind AI.

Implements a CVSS-aligned, context-aware risk scoring system that:
- Normalises AI-generated scores and validates them
- Applies business context modifiers (environment, data sensitivity, exposure)
- Computes aggregate risk scores across multiple findings
- Categorises overall posture into risk bands
- Provides a detailed score breakdown for audit trails
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from ai.models.schemas import Finding, FindingSeverity, RiskScore


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Severity → CVSS base score floor mapping
_SEVERITY_BASE_SCORE_MAP: Dict[FindingSeverity, float] = {
    FindingSeverity.CRITICAL: 9.0,
    FindingSeverity.HIGH: 7.0,
    FindingSeverity.MEDIUM: 4.0,
    FindingSeverity.LOW: 0.1,
    FindingSeverity.INFO: 0.0,
}

# Severity → CVSS base score ceiling mapping
_SEVERITY_BASE_SCORE_CEILING: Dict[FindingSeverity, float] = {
    FindingSeverity.CRITICAL: 10.0,
    FindingSeverity.HIGH: 8.9,
    FindingSeverity.MEDIUM: 6.9,
    FindingSeverity.LOW: 3.9,
    FindingSeverity.INFO: 0.0,
}


class RiskBand(str, Enum):
    """Human-readable risk band for an overall posture score."""

    CRITICAL = "critical"     # 9.0 – 10.0
    HIGH = "high"             # 7.0 – 8.9
    MEDIUM = "medium"         # 4.0 – 6.9
    LOW = "low"               # 0.1 – 3.9
    NEGLIGIBLE = "negligible" # 0.0


class EnvironmentModifier(str, Enum):
    """Business context: how critical is the environment being analysed."""

    PRODUCTION = "production"         # modifier: 1.0  (no discount)
    STAGING = "staging"               # modifier: 0.85
    DEVELOPMENT = "development"       # modifier: 0.70
    SANDBOX = "sandbox"               # modifier: 0.55


class DataSensitivity(str, Enum):
    """Sensitivity of data handled by the resource."""

    PCI = "pci"           # Payment card data   → modifier: 1.2
    PII = "pii"           # Personal data        → modifier: 1.15
    PHI = "phi"           # Health data          → modifier: 1.2
    CONFIDENTIAL = "confidential"  # Internal sensitive  → modifier: 1.0
    INTERNAL = "internal"         # General internal    → modifier: 0.85
    PUBLIC = "public"             # Publicly shared     → modifier: 0.7


_ENV_MODIFIER: Dict[EnvironmentModifier, float] = {
    EnvironmentModifier.PRODUCTION: 1.0,
    EnvironmentModifier.STAGING: 0.85,
    EnvironmentModifier.DEVELOPMENT: 0.70,
    EnvironmentModifier.SANDBOX: 0.55,
}

_DATA_SENSITIVITY_MODIFIER: Dict[DataSensitivity, float] = {
    DataSensitivity.PCI: 1.20,
    DataSensitivity.PHI: 1.20,
    DataSensitivity.PII: 1.15,
    DataSensitivity.CONFIDENTIAL: 1.00,
    DataSensitivity.INTERNAL: 0.85,
    DataSensitivity.PUBLIC: 0.70,
}


# ---------------------------------------------------------------------------
# Score breakdown dataclass
# ---------------------------------------------------------------------------

@dataclass
class ScoringBreakdown:
    """Detailed breakdown of how an adjusted risk score was computed."""

    finding_id: str
    raw_base_score: float
    exploitability: float
    impact: float
    raw_overall_score: float
    environment_modifier: float
    data_sensitivity_modifier: float
    exposure_modifier: float
    adjusted_score: float
    severity: FindingSeverity
    risk_band: RiskBand
    notes: List[str] = field(default_factory=list)


@dataclass
class AggregateRiskResult:
    """Aggregated risk across all findings."""

    overall_score: float
    risk_band: RiskBand
    finding_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    info_count: int
    breakdowns: List[ScoringBreakdown]
    weighted_average: float

    @property
    def has_critical(self) -> bool:
        return self.critical_count > 0

    @property
    def has_high(self) -> bool:
        return self.high_count > 0


# ---------------------------------------------------------------------------
# Scoring engine
# ---------------------------------------------------------------------------

class RiskScoringEngine:
    """
    Computes and adjusts risk scores for infrastructure findings.

    Usage::

        engine = RiskScoringEngine(
            environment=EnvironmentModifier.PRODUCTION,
            data_sensitivity=DataSensitivity.PII,
            internet_exposed=True,
        )
        result = engine.aggregate(findings)
        print(result.overall_score, result.risk_band)
    """

    def __init__(
        self,
        environment: EnvironmentModifier = EnvironmentModifier.PRODUCTION,
        data_sensitivity: DataSensitivity = DataSensitivity.INTERNAL,
        internet_exposed: bool = False,
    ) -> None:
        self.environment = environment
        self.data_sensitivity = data_sensitivity
        self.internet_exposed = internet_exposed

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score_finding(self, finding: Finding) -> ScoringBreakdown:
        """
        Compute an adjusted risk score for a single finding.

        The adjusted score is capped at 10.0 and clipped at 0.0.
        """
        rs = finding.risk_score
        raw_overall = rs.overall_score if rs.overall_score is not None else (
            rs.base_score * rs.exploitability * rs.impact
        )

        env_mod = _ENV_MODIFIER[self.environment]
        sensitivity_mod = _DATA_SENSITIVITY_MODIFIER[self.data_sensitivity]
        exposure_mod = 1.15 if self.internet_exposed else 1.0

        adjusted = min(10.0, max(0.0, raw_overall * env_mod * sensitivity_mod * exposure_mod))
        adjusted = round(adjusted, 2)

        notes: List[str] = []
        if env_mod < 1.0:
            notes.append(f"Environment modifier {env_mod} applied for {self.environment.value}")
        if sensitivity_mod != 1.0:
            notes.append(f"Data sensitivity modifier {sensitivity_mod} applied for {self.data_sensitivity.value}")
        if exposure_mod > 1.0:
            notes.append("Internet exposure modifier applied")

        return ScoringBreakdown(
            finding_id=finding.id,
            raw_base_score=rs.base_score,
            exploitability=rs.exploitability,
            impact=rs.impact,
            raw_overall_score=round(raw_overall, 2),
            environment_modifier=env_mod,
            data_sensitivity_modifier=sensitivity_mod,
            exposure_modifier=exposure_mod,
            adjusted_score=adjusted,
            severity=finding.severity,
            risk_band=score_to_risk_band(adjusted),
            notes=notes,
        )

    def aggregate(self, findings: List[Finding]) -> AggregateRiskResult:
        """
        Aggregate risk scores across all findings.

        The overall score is the *maximum* adjusted score (worst-case posture),
        while the weighted average is also computed for trend analysis.
        """
        if not findings:
            return AggregateRiskResult(
                overall_score=0.0,
                risk_band=RiskBand.NEGLIGIBLE,
                finding_count=0,
                critical_count=0,
                high_count=0,
                medium_count=0,
                low_count=0,
                info_count=0,
                breakdowns=[],
                weighted_average=0.0,
            )

        breakdowns = [self.score_finding(f) for f in findings]
        adjusted_scores = [b.adjusted_score for b in breakdowns]

        overall_score = round(max(adjusted_scores), 2)
        weighted_average = round(_weighted_mean(adjusted_scores), 2)

        counts: Dict[FindingSeverity, int] = {s: 0 for s in FindingSeverity}
        for f in findings:
            counts[f.severity] += 1

        return AggregateRiskResult(
            overall_score=overall_score,
            risk_band=score_to_risk_band(overall_score),
            finding_count=len(findings),
            critical_count=counts[FindingSeverity.CRITICAL],
            high_count=counts[FindingSeverity.HIGH],
            medium_count=counts[FindingSeverity.MEDIUM],
            low_count=counts[FindingSeverity.LOW],
            info_count=counts[FindingSeverity.INFO],
            breakdowns=breakdowns,
            weighted_average=weighted_average,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _reconcile_with_severity(score: float, severity: FindingSeverity) -> float:
        """
        Ensure the adjusted score falls within the expected range for the severity.

        If the AI assigns a severity label that is inconsistent with the numeric
        score, we clip to the appropriate floor/ceiling rather than trusting
        either blindly.
        """
        floor = _SEVERITY_BASE_SCORE_MAP[severity]
        ceiling = _SEVERITY_BASE_SCORE_CEILING[severity]
        return round(min(ceiling, max(floor, score)), 2)

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_context(cls, context: Dict) -> RiskScoringEngine:
        """
        Create an engine from a context dictionary (as stored in AnalysisRequest.context).

        Expected keys (all optional):
        - ``environment``:       one of EnvironmentModifier values
        - ``data_sensitivity``:  one of DataSensitivity values
        - ``internet_exposed``:  bool
        """
        env_str = context.get("environment", EnvironmentModifier.PRODUCTION.value)
        sensitivity_str = context.get("data_sensitivity", DataSensitivity.INTERNAL.value)
        internet_exposed = bool(context.get("internet_exposed", False))

        try:
            env = EnvironmentModifier(env_str)
        except ValueError:
            env = EnvironmentModifier.PRODUCTION

        try:
            sensitivity = DataSensitivity(sensitivity_str)
        except ValueError:
            sensitivity = DataSensitivity.INTERNAL

        return cls(
            environment=env,
            data_sensitivity=sensitivity,
            internet_exposed=internet_exposed,
        )


# ---------------------------------------------------------------------------
# Standalone helpers
# ---------------------------------------------------------------------------


def score_to_risk_band(score: float) -> RiskBand:
    """Map a numeric score (0–10) to a ``RiskBand``."""
    if score >= 9.0:
        return RiskBand.CRITICAL
    if score >= 7.0:
        return RiskBand.HIGH
    if score >= 4.0:
        return RiskBand.MEDIUM
    if score > 0.0:
        return RiskBand.LOW
    return RiskBand.NEGLIGIBLE


def severity_from_score(score: float) -> FindingSeverity:
    """Derive a ``FindingSeverity`` from a numeric CVSS-style score."""
    if score >= 9.0:
        return FindingSeverity.CRITICAL
    if score >= 7.0:
        return FindingSeverity.HIGH
    if score >= 4.0:
        return FindingSeverity.MEDIUM
    if score > 0.0:
        return FindingSeverity.LOW
    return FindingSeverity.INFO


def _weighted_mean(scores: List[float]) -> float:
    """
    Compute a severity-weighted mean.

    Higher scores are weighted exponentially more to reflect that a single
    critical finding dominates the overall risk posture.
    """
    if not scores:
        return 0.0
    weights = [math.exp(s) for s in scores]
    total_weight = sum(weights)
    return sum(s * w for s, w in zip(scores, weights)) / total_weight
