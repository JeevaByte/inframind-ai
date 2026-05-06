from __future__ import annotations

"""Mock AI service that returns deterministic, rule-based findings.

In production this module would be replaced (or extended) to call a real LLM
or a dedicated scanning micro-service via HTTP.  All public contracts are kept
identical so the swap is transparent to callers.
"""

import re
import uuid
from typing import Any, Dict, List, Tuple

from app.models.common import AnalysisType, Finding, InfraFileType, Severity

# ---------------------------------------------------------------------------
# Rule definitions
# ---------------------------------------------------------------------------

_SECURITY_RULES = [
    {
        "rule_id": "SEC-001",
        "title": "Hard-coded credentials detected",
        "description": "A potential hard-coded secret (password, key, token) was found in the file.",
        "severity": Severity.CRITICAL,
        "pattern": re.compile(
            r'(password|secret|token|api_key|access_key)\s*[=:]\s*["\']?[A-Za-z0-9+/]{8,}',
            re.IGNORECASE,
        ),
        "recommendation": "Use environment variables or a secrets manager instead of hard-coding credentials.",
        "references": ["https://owasp.org/www-community/vulnerabilities/Use_of_hard-coded_credentials"],
    },
    {
        "rule_id": "SEC-002",
        "title": "Publicly accessible resource",
        "description": 'A resource appears to be exposed to the public internet (0.0.0.0/0 or "0.0.0.0").',
        "severity": Severity.HIGH,
        "pattern": re.compile(r"0\.0\.0\.0/0|cidr_blocks\s*=\s*\[\"0\.0\.0\.0/0\"\]", re.IGNORECASE),
        "recommendation": "Restrict access to specific IP ranges or use a VPN / private networking.",
        "references": ["https://docs.aws.amazon.com/vpc/latest/userguide/security-groups.html"],
    },
    {
        "rule_id": "SEC-003",
        "title": "Encryption disabled",
        "description": "A resource has encryption explicitly disabled or not enabled.",
        "severity": Severity.HIGH,
        "pattern": re.compile(r"encrypted\s*=\s*false|encryption\s*=\s*false", re.IGNORECASE),
        "recommendation": "Enable encryption at rest and in transit for all sensitive data stores.",
        "references": ["https://csrc.nist.gov/publications/detail/sp/800-111/final"],
    },
    {
        "rule_id": "SEC-004",
        "title": "Root / admin privileges granted",
        "description": "The configuration grants root or wildcard (*) administrative permissions.",
        "severity": Severity.CRITICAL,
        "pattern": re.compile(r'"Action"\s*:\s*"\*"|effect\s*=\s*"Allow".*\*', re.IGNORECASE | re.DOTALL),
        "recommendation": "Apply the principle of least privilege; grant only the permissions required.",
        "references": ["https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html"],
    },
]

_COST_RULES = [
    {
        "rule_id": "COST-001",
        "title": "Large instance type detected",
        "description": "An instance type with high vCPU / memory count is provisioned; verify it is necessary.",
        "severity": Severity.MEDIUM,
        "pattern": re.compile(r"\b(x1e|x2iedn|u-\d+tb|p4de|trn1)\.\S+", re.IGNORECASE),
        "recommendation": "Right-size the instance based on actual workload metrics.",
        "references": ["https://aws.amazon.com/ec2/instance-types/"],
    },
    {
        "rule_id": "COST-002",
        "title": "No auto-scaling configured",
        "description": "Resources are statically provisioned with no auto-scaling policy detected.",
        "severity": Severity.LOW,
        "pattern": re.compile(r"desired_capacity\s*=\s*\d+", re.IGNORECASE),
        "recommendation": "Add an auto-scaling policy to dynamically adjust capacity and reduce costs.",
        "references": ["https://docs.aws.amazon.com/autoscaling/ec2/userguide/what-is-amazon-ec2-auto-scaling.html"],
    },
]

_COMPLIANCE_RULES = [
    {
        "rule_id": "COMP-001",
        "title": "Missing resource tags",
        "description": "One or more resources are missing mandatory tags (e.g., Owner, Environment, CostCenter).",
        "severity": Severity.MEDIUM,
        "pattern": re.compile(r"tags\s*=\s*\{\}", re.IGNORECASE),
        "recommendation": "Add mandatory tags to all resources to support cost allocation and governance.",
        "references": ["https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html"],
    },
    {
        "rule_id": "COMP-002",
        "title": "Logging not enabled",
        "description": "Access logging or audit logging is not explicitly enabled on this resource.",
        "severity": Severity.HIGH,
        "pattern": re.compile(r"logging\s*=\s*false|enable_logging\s*=\s*false", re.IGNORECASE),
        "recommendation": "Enable access and audit logging to meet compliance requirements.",
        "references": ["https://docs.aws.amazon.com/AmazonS3/latest/userguide/ServerLogs.html"],
    },
    {
        "rule_id": "COMP-003",
        "title": "MFA delete not enabled on S3 bucket",
        "description": "The S3 bucket does not have MFA delete enabled.",
        "severity": Severity.MEDIUM,
        "pattern": re.compile(r'aws_s3_bucket(?!.*mfa_delete\s*=\s*"Enabled")', re.IGNORECASE | re.DOTALL),
        "recommendation": "Enable MFA delete on S3 buckets containing sensitive data.",
        "references": ["https://docs.aws.amazon.com/AmazonS3/latest/userguide/MultiFactorAuthenticationDelete.html"],
    },
]

_RULES_BY_TYPE: Dict[AnalysisType, list] = {
    AnalysisType.SECURITY: _SECURITY_RULES,
    AnalysisType.COST: _COST_RULES,
    AnalysisType.COMPLIANCE: _COMPLIANCE_RULES,
    AnalysisType.FULL: _SECURITY_RULES + _COST_RULES + _COMPLIANCE_RULES,
}

_SEVERITY_WEIGHTS = {
    Severity.CRITICAL: 25,
    Severity.HIGH: 15,
    Severity.MEDIUM: 8,
    Severity.LOW: 3,
    Severity.INFO: 1,
}


def _run_rules(content: str, rules: list) -> List[Finding]:
    findings: List[Finding] = []
    lines = content.splitlines()

    for rule in rules:
        pattern: re.Pattern = rule["pattern"]
        for line_no, line in enumerate(lines, start=1):
            if pattern.search(line):
                findings.append(
                    Finding(
                        id=str(uuid.uuid4()),
                        rule_id=rule["rule_id"],
                        title=rule["title"],
                        description=rule["description"],
                        severity=rule["severity"],
                        line_number=line_no,
                        recommendation=rule["recommendation"],
                        references=rule["references"],
                    )
                )
                # One finding per rule (first match) to avoid flooding
                break

    return findings


def _compute_score(findings: List[Finding]) -> float:
    """Return a 0-100 security / quality score (100 = no findings)."""
    if not findings:
        return 100.0
    penalty = sum(_SEVERITY_WEIGHTS.get(f.severity, 0) for f in findings)
    score = max(0.0, 100.0 - penalty)
    return round(score, 1)


def _build_summary(findings: List[Finding], analysis_type: AnalysisType) -> str:
    if not findings:
        return f"No issues found during {analysis_type.value} analysis. The file looks good!"

    counts: Dict[Severity, int] = {}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1

    parts = [f"{v} {k.value}" for k, v in counts.items()]
    return (
        f"Analysis type: {analysis_type.value}. "
        f"Found {len(findings)} issue(s): {', '.join(parts)}. "
        "Review the findings and apply the recommended remediations."
    )


class MockAIService:
    """Deterministic mock AI service for local development and testing."""

    async def analyze(
        self,
        content: str,
        file_type: InfraFileType,
        analysis_type: AnalysisType,
        options: Dict[str, Any],
    ) -> Tuple[List[Finding], str, float]:
        rules = _RULES_BY_TYPE.get(analysis_type, _SECURITY_RULES + _COST_RULES + _COMPLIANCE_RULES)
        findings = _run_rules(content, rules)
        score = _compute_score(findings)
        summary = _build_summary(findings, analysis_type)
        return findings, summary, score
