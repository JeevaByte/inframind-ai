"""
Pydantic data models for InfraMind AI.

These schemas are used throughout the prompt, orchestration, risk-scoring,
and recommendation modules to provide a consistent data contract.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class ResourceType(str, Enum):
    """Supported infrastructure resource categories."""

    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    DATABASE = "database"
    IAM = "iam"
    CONTAINER = "container"
    SERVERLESS = "serverless"
    MESSAGING = "messaging"
    MONITORING = "monitoring"
    OTHER = "other"


class FindingSeverity(str, Enum):
    """CVSS-aligned severity levels for a security or configuration finding."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RemediationPriority(str, Enum):
    """Priority level assigned to a remediation recommendation."""

    IMMEDIATE = "immediate"    # Fix now — active risk
    HIGH = "high"              # Fix within 24 hours
    MEDIUM = "medium"          # Fix within 7 days
    LOW = "low"                # Fix in next sprint / maintenance window
    DEFERRED = "deferred"      # Nice-to-have, no active risk


class CloudProvider(str, Enum):
    """Supported cloud providers."""

    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    ON_PREM = "on_prem"
    MULTI_CLOUD = "multi_cloud"
    OTHER = "other"


# ---------------------------------------------------------------------------
# Core domain models
# ---------------------------------------------------------------------------


class InfraResource(BaseModel):
    """A single infrastructure resource to be analysed."""

    id: str = Field(..., description="Unique identifier for this resource (e.g. ARN, resource ID).")
    name: str = Field(..., description="Human-readable resource name.")
    resource_type: ResourceType = Field(..., description="Category of the resource.")
    provider: CloudProvider = Field(default=CloudProvider.AWS, description="Cloud provider.")
    region: Optional[str] = Field(default=None, description="Deployment region or zone.")
    tags: Dict[str, str] = Field(default_factory=dict, description="Provider tags/labels.")
    configuration: Dict[str, Any] = Field(
        default_factory=dict,
        description="Raw provider configuration snapshot (e.g. EC2 describe-instances output).",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context such as cost data, usage metrics, or compliance flags.",
    )

    model_config = {"extra": "allow"}


class RiskScore(BaseModel):
    """
    Quantitative risk score for a finding.

    The overall score (0–10) is derived from the base score, adjusted by
    exploitability and impact factors, then optionally weighted by business
    context.
    """

    base_score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Base CVSS-style score (0–10).",
    )
    exploitability: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Exploitability multiplier (0 = not exploitable, 1 = trivially exploitable).",
    )
    impact: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Business/operational impact multiplier.",
    )
    overall_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=10.0,
        description="Computed overall score. Auto-calculated if not supplied.",
    )
    rationale: str = Field(default="", description="Brief explanation of the score.")

    def model_post_init(self, __context: Any) -> None:
        if self.overall_score is None:
            self.overall_score = round(
                min(10.0, self.base_score * self.exploitability * self.impact), 2
            )


class Finding(BaseModel):
    """A single security or misconfiguration finding on a resource."""

    id: str = Field(..., description="Unique finding identifier.")
    resource_id: str = Field(..., description="ID of the affected InfraResource.")
    title: str = Field(..., description="Short, descriptive title.")
    description: str = Field(..., description="Detailed description of the finding.")
    severity: FindingSeverity = Field(..., description="Severity level.")
    risk_score: RiskScore = Field(..., description="Quantitative risk assessment.")
    cve_ids: List[str] = Field(default_factory=list, description="Related CVE identifiers.")
    compliance_frameworks: List[str] = Field(
        default_factory=list,
        description="Compliance frameworks affected (e.g. CIS, SOC2, PCI-DSS).",
    )
    affected_attribute: Optional[str] = Field(
        default=None,
        description="Specific configuration attribute that triggered the finding.",
    )
    evidence: Optional[str] = Field(
        default=None, description="Raw evidence or configuration snippet."
    )
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)


class Recommendation(BaseModel):
    """An actionable remediation recommendation linked to one or more findings."""

    id: str = Field(..., description="Unique recommendation identifier.")
    finding_ids: List[str] = Field(..., description="Finding IDs addressed by this recommendation.")
    title: str = Field(..., description="Short recommendation title.")
    description: str = Field(..., description="Detailed remediation guidance.")
    priority: RemediationPriority = Field(..., description="Remediation priority.")
    effort: str = Field(
        default="medium",
        description="Estimated effort (low / medium / high / very-high).",
    )
    steps: List[str] = Field(default_factory=list, description="Step-by-step remediation actions.")
    references: List[str] = Field(
        default_factory=list, description="Links to documentation or advisories."
    )
    auto_remediable: bool = Field(
        default=False,
        description="Whether this recommendation can be applied automatically.",
    )
    automation_script: Optional[str] = Field(
        default=None, description="IaC or CLI snippet for automated remediation."
    )

    @field_validator("effort")
    @classmethod
    def validate_effort(cls, v: str) -> str:
        allowed = {"low", "medium", "high", "very-high"}
        if v.lower() not in allowed:
            raise ValueError(f"effort must be one of {allowed}")
        return v.lower()


class AnalysisResult(BaseModel):
    """The complete result returned by the AI orchestrator for one analysis run."""

    request_id: str = Field(..., description="Identifier correlating back to the AnalysisRequest.")
    resources_analysed: int = Field(..., description="Number of resources analysed.")
    findings: List[Finding] = Field(default_factory=list)
    recommendations: List[Recommendation] = Field(default_factory=list)
    summary: str = Field(default="", description="Executive summary generated by the AI.")
    overall_risk_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=10.0,
        description="Aggregated risk score across all findings.",
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def model_post_init(self, __context: Any) -> None:
        if self.overall_risk_score is None and self.findings:
            scores = [f.risk_score.overall_score for f in self.findings if f.risk_score.overall_score is not None]
            self.overall_risk_score = round(max(scores), 2) if scores else None


class AnalysisRequest(BaseModel):
    """Input request to the AI orchestrator."""

    request_id: str = Field(..., description="Unique request identifier.")
    resources: List[InfraResource] = Field(..., min_length=1)
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional context such as environment name, owner team, or compliance requirements.",
    )
    focus_areas: List[str] = Field(
        default_factory=list,
        description="Optional list of analysis focus areas (e.g. 'encryption', 'network-exposure').",
    )
    provider_hint: Optional[CloudProvider] = Field(
        default=None, description="Primary cloud provider hint for prompt selection."
    )
    max_findings: Optional[int] = Field(
        default=None,
        ge=1,
        description="Cap on the number of findings to return.",
    )
