"""
Recommendation engine for InfraMind AI.

Transforms raw findings into prioritised, actionable, de-duplicated recommendations.

Responsibilities:
- Consolidate multiple findings that share the same root cause
- Map common finding patterns to well-known remediation playbooks
- Assign priority based on risk score + business context
- Estimate remediation effort
- Attach IaC / CLI automation snippets where available
- Enrich recommendations with external references (documentation, advisories)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ai.models.schemas import (
    Finding,
    FindingSeverity,
    Recommendation,
    RemediationPriority,
    ResourceType,
    RiskScore,
)


# ---------------------------------------------------------------------------
# Playbook definitions
# ---------------------------------------------------------------------------

@dataclass
class RemediationPlaybook:
    """
    A pre-defined remediation playbook for a known finding pattern.

    Playbooks are matched against findings by keyword patterns in the finding
    title or affected_attribute, allowing the engine to augment AI-generated
    recommendations with curated guidance.
    """

    playbook_id: str
    title: str
    description: str
    effort: str
    steps: List[str]
    references: List[str]
    auto_remediable: bool = False
    automation_script: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    resource_types: List[ResourceType] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Built-in playbooks
# ---------------------------------------------------------------------------

_PLAYBOOKS: List[RemediationPlaybook] = [
    RemediationPlaybook(
        playbook_id="PB-S3-PUBLIC-ACCESS",
        title="Enable S3 Block Public Access",
        description=(
            "Enable all four S3 Block Public Access settings at the bucket level "
            "to prevent unintended public exposure of stored data."
        ),
        effort="low",
        steps=[
            "Navigate to the S3 bucket in the AWS Console.",
            "Click 'Permissions' → 'Block public access (bucket settings)'.",
            "Enable all four settings: BlockPublicAcls, IgnorePublicAcls, "
            "BlockPublicPolicy, RestrictPublicBuckets.",
            "Apply the same settings at the account level via "
            "aws s3control put-public-access-block.",
            "Verify no bucket policy grants public read/write access.",
        ],
        references=[
            "https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html",
            "https://www.cisecurity.org/benchmark/amazon_web_services",
        ],
        auto_remediable=True,
        automation_script=(
            "aws s3api put-public-access-block \\\n"
            "  --bucket YOUR_BUCKET_NAME \\\n"
            "  --public-access-block-configuration "
            "BlockPublicAcls=true,IgnorePublicAcls=true,"
            "BlockPublicPolicy=true,RestrictPublicBuckets=true"
        ),
        keywords=["public access", "publicly accessible", "bucket public"],
        resource_types=[ResourceType.STORAGE],
    ),
    RemediationPlaybook(
        playbook_id="PB-S3-ENCRYPTION",
        title="Enable S3 Server-Side Encryption",
        description=(
            "Configure default server-side encryption on the S3 bucket using "
            "AES-256 (SSE-S3) or AWS KMS (SSE-KMS)."
        ),
        effort="low",
        steps=[
            "Navigate to the S3 bucket → 'Properties' → 'Default encryption'.",
            "Select 'AWS-KMS' and choose or create a KMS key.",
            "Enforce encryption via bucket policy: deny s3:PutObject without "
            "x-amz-server-side-encryption header.",
            "Enable Macie to detect unencrypted sensitive data.",
        ],
        references=[
            "https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-encryption.html",
        ],
        auto_remediable=True,
        automation_script=(
            "aws s3api put-bucket-encryption \\\n"
            "  --bucket YOUR_BUCKET_NAME \\\n"
            "  --server-side-encryption-configuration '{"
            '"Rules":[{"ApplyServerSideEncryptionByDefault":'
            '{"SSEAlgorithm":"aws:kms"}}]}' + "'"
        ),
        keywords=["encryption", "encrypt at rest", "sse"],
        resource_types=[ResourceType.STORAGE],
    ),
    RemediationPlaybook(
        playbook_id="PB-EC2-IMDSV2",
        title="Enforce IMDSv2 on EC2 Instances",
        description=(
            "Configure EC2 instances to require IMDSv2 (session-oriented requests) "
            "to prevent SSRF-based metadata credential theft."
        ),
        effort="low",
        steps=[
            "Run: aws ec2 modify-instance-metadata-options --instance-id <id> "
            "--http-tokens required --http-endpoint enabled",
            "Update launch templates / auto-scaling groups to enforce IMDSv2 by default.",
            "Monitor IMDSv1 usage via CloudWatch metric MetadataNoToken.",
        ],
        references=[
            "https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html",
            "https://aws.amazon.com/blogs/security/defense-in-depth-open-firewalls-reverse-proxies-ssrf-vulnerabilities-ec2-instance-metadata-service/",
        ],
        auto_remediable=True,
        automation_script=(
            "aws ec2 modify-instance-metadata-options \\\n"
            "  --instance-id YOUR_INSTANCE_ID \\\n"
            "  --http-tokens required \\\n"
            "  --http-endpoint enabled"
        ),
        keywords=["imds", "imdsv2", "metadata service", "ssrf"],
        resource_types=[ResourceType.COMPUTE],
    ),
    RemediationPlaybook(
        playbook_id="PB-IAM-MFA",
        title="Enforce MFA for IAM Users",
        description=(
            "Enable multi-factor authentication for all IAM users with console access "
            "and the root account."
        ),
        effort="medium",
        steps=[
            "Enable MFA for the root account via IAM → Security credentials.",
            "Create an IAM policy that denies all actions if MFA is not authenticated "
            "(Condition: aws:MultiFactorAuthPresent = false), and attach it to all users.",
            "Use AWS Config rule 'iam-user-mfa-enabled' to detect non-compliant users.",
            "Enable IAM Access Analyzer to detect unused credentials.",
        ],
        references=[
            "https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_mfa.html",
            "https://www.cisecurity.org/benchmark/amazon_web_services",
        ],
        keywords=["mfa", "multi-factor", "two-factor", "2fa"],
        resource_types=[ResourceType.IAM],
    ),
    RemediationPlaybook(
        playbook_id="PB-RDS-PUBLIC",
        title="Disable RDS Public Accessibility",
        description=(
            "Ensure RDS instances are not publicly accessible and are placed in "
            "private subnets."
        ),
        effort="medium",
        steps=[
            "Modify the RDS instance: set PubliclyAccessible = false.",
            "Move the instance to a private subnet group (requires a snapshot restore "
            "if changing VPC).",
            "Update security groups to allow access only from the application tier "
            "security group.",
            "Enable RDS encryption and audit logging.",
        ],
        references=[
            "https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.IAM.html",
        ],
        auto_remediable=True,
        automation_script=(
            "aws rds modify-db-instance \\\n"
            "  --db-instance-identifier YOUR_DB_ID \\\n"
            "  --no-publicly-accessible \\\n"
            "  --apply-immediately"
        ),
        keywords=["rds public", "database public", "publicly accessible"],
        resource_types=[ResourceType.DATABASE],
    ),
    RemediationPlaybook(
        playbook_id="PB-SG-OPEN-SSH",
        title="Restrict SSH Access (Port 22)",
        description=(
            "Remove inbound 0.0.0.0/0 rules on port 22 and replace with "
            "IP-restricted access or use AWS Systems Manager Session Manager."
        ),
        effort="low",
        steps=[
            "Identify the security group rule allowing 0.0.0.0/0 on port 22.",
            "Remove the rule: aws ec2 revoke-security-group-ingress ...",
            "Replace with: restrict to your corporate IP CIDR, or",
            "Migrate to SSM Session Manager for agent-based access (no SSH required).",
            "Audit other security groups for similar permissive rules.",
        ],
        references=[
            "https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html",
        ],
        keywords=["ssh", "port 22", "open ssh", "rdp", "port 3389"],
        resource_types=[ResourceType.COMPUTE, ResourceType.NETWORK],
    ),
    RemediationPlaybook(
        playbook_id="PB-SECRETS-IN-CONFIG",
        title="Remove Hard-Coded Secrets from Configuration",
        description=(
            "Migrate credentials and secrets from configuration files / environment "
            "variables to a dedicated secrets management service."
        ),
        effort="high",
        steps=[
            "Rotate all exposed credentials immediately.",
            "Move secrets to AWS Secrets Manager or Parameter Store (SecureString).",
            "Update application code to retrieve secrets at runtime via SDK calls.",
            "Scan IaC templates and source code with tools like truffleHog or git-secrets.",
            "Add pre-commit hooks to prevent future secret commits.",
            "Enable GuardDuty credential exfiltration detection.",
        ],
        references=[
            "https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html",
            "https://github.com/trufflesecurity/trufflehog",
        ],
        keywords=["secret", "credential", "password", "api key", "token", "hard-coded"],
    ),
    RemediationPlaybook(
        playbook_id="PB-LOGGING-DISABLED",
        title="Enable Access Logging and Monitoring",
        description=(
            "Enable comprehensive access logging and monitoring to support "
            "incident detection, investigation, and compliance."
        ),
        effort="low",
        steps=[
            "Enable CloudTrail for all regions with log file validation.",
            "Enable S3 server access logging to a dedicated log bucket.",
            "Enable VPC Flow Logs to an S3 bucket or CloudWatch Logs.",
            "Configure CloudWatch alarms for critical API calls and threshold breaches.",
            "Set log retention policies appropriate to compliance requirements.",
        ],
        references=[
            "https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-user-guide.html",
        ],
        keywords=["logging", "monitoring", "audit", "cloudtrail", "flow logs"],
    ),
    RemediationPlaybook(
        playbook_id="PB-K8S-RBAC",
        title="Implement Kubernetes RBAC Least Privilege",
        description=(
            "Audit and tighten Kubernetes RBAC to ensure pods and service accounts "
            "have only the permissions they require."
        ),
        effort="high",
        steps=[
            "Audit existing ClusterRoles and Roles: kubectl get clusterroles,roles -A",
            "Remove wildcard ('*') verbs and resources from custom roles.",
            "Bind roles at the namespace level (RoleBinding) not cluster level "
            "unless truly required.",
            "Use dedicated service accounts per workload; avoid mounting the default "
            "service account token.",
            "Enable Pod Security Admission with 'Restricted' profile.",
            "Periodically review with tools like rbac-tool or kube-bench.",
        ],
        references=[
            "https://kubernetes.io/docs/reference/access-authn-authz/rbac/",
            "https://github.com/aquasecurity/kube-bench",
        ],
        keywords=["rbac", "cluster role", "role binding", "kubernetes", "k8s"],
        resource_types=[ResourceType.CONTAINER],
    ),
]

# Index playbooks by keyword for fast lookup
_KEYWORD_INDEX: Dict[str, List[RemediationPlaybook]] = {}
for _pb in _PLAYBOOKS:
    for _kw in _pb.keywords:
        _KEYWORD_INDEX.setdefault(_kw.lower(), []).append(_pb)


# ---------------------------------------------------------------------------
# Priority mapping
# ---------------------------------------------------------------------------

def _score_to_priority(score: float) -> RemediationPriority:
    if score >= 9.0:
        return RemediationPriority.IMMEDIATE
    if score >= 7.0:
        return RemediationPriority.HIGH
    if score >= 4.0:
        return RemediationPriority.MEDIUM
    if score > 0.0:
        return RemediationPriority.LOW
    return RemediationPriority.DEFERRED


# ---------------------------------------------------------------------------
# Recommendation engine
# ---------------------------------------------------------------------------

class RecommendationEngine:
    """
    Transforms a list of findings into prioritised, de-duplicated recommendations.

    The engine:
    1. Groups findings with the same root cause (title similarity + resource type).
    2. Looks up pre-defined playbooks for common patterns.
    3. Derives priority from the maximum risk score across grouped findings.
    4. Enriches AI-generated recommendations with playbook steps and references.

    Usage::

        engine = RecommendationEngine()
        recommendations = engine.generate(findings)
    """

    def generate(
        self,
        findings: List[Finding],
        existing_recommendations: Optional[List[Recommendation]] = None,
    ) -> List[Recommendation]:
        """
        Generate recommendations from findings.

        Parameters
        ----------
        findings:
            List of ``Finding`` objects to process.
        existing_recommendations:
            Optional list of AI-generated recommendations to enrich rather than
            replace.  When provided, the engine will augment them with playbook
            data and fill gaps.

        Returns
        -------
        List[Recommendation]
            Sorted list of recommendations (immediate first).
        """
        # If existing recommendations are provided, enrich them
        if existing_recommendations:
            enriched = [self._enrich(rec, findings) for rec in existing_recommendations]
            generated = self._generate_from_findings(findings, existing_recommendations)
            all_recs = enriched + generated
        else:
            all_recs = self._generate_from_findings(findings, [])

        # De-duplicate by title
        seen_titles: set[str] = set()
        deduped: List[Recommendation] = []
        for rec in all_recs:
            if rec.title not in seen_titles:
                seen_titles.add(rec.title)
                deduped.append(rec)

        return sorted(deduped, key=lambda r: list(RemediationPriority).index(r.priority))

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _enrich(
        self, rec: Recommendation, findings: List[Finding]
    ) -> Recommendation:
        """Enrich an AI-generated recommendation with playbook data."""
        playbook = self._find_playbook(rec.title + " " + rec.description)
        if playbook is None:
            return rec

        # Merge playbook steps and references into the AI recommendation
        merged_steps = rec.steps or playbook.steps
        merged_refs = list(set((rec.references or []) + playbook.references))

        return Recommendation(
            id=rec.id,
            finding_ids=rec.finding_ids,
            title=rec.title,
            description=rec.description or playbook.description,
            priority=rec.priority,
            effort=rec.effort or playbook.effort,
            steps=merged_steps,
            references=merged_refs,
            auto_remediable=rec.auto_remediable or playbook.auto_remediable,
            automation_script=rec.automation_script or playbook.automation_script,
        )

    def _generate_from_findings(
        self,
        findings: List[Finding],
        existing_recs: List[Recommendation],
    ) -> List[Recommendation]:
        """Generate new recommendations for findings not covered by existing ones."""
        covered_finding_ids = {fid for rec in existing_recs for fid in rec.finding_ids}
        uncovered = [f for f in findings if f.id not in covered_finding_ids]

        # Group by playbook match (or create a 1-finding recommendation if no playbook)
        groups: Dict[str, List[Finding]] = {}  # playbook_id / "finding-<id>" → findings
        playbook_map: Dict[str, Optional[RemediationPlaybook]] = {}

        for finding in uncovered:
            playbook = self._find_playbook(
                finding.title + " " + (finding.affected_attribute or "")
            )
            if playbook:
                key = playbook.playbook_id
                playbook_map[key] = playbook
            else:
                key = f"finding-{finding.id}"
                playbook_map[key] = None
            groups.setdefault(key, []).append(finding)

        recs: List[Recommendation] = []
        for key, group_findings in groups.items():
            pb = playbook_map[key]
            max_score = max(
                (f.risk_score.overall_score or 0.0) for f in group_findings
            )
            priority = _score_to_priority(max_score)

            if pb:
                recs.append(
                    Recommendation(
                        id=str(uuid.uuid4()),
                        finding_ids=[f.id for f in group_findings],
                        title=pb.title,
                        description=pb.description,
                        priority=priority,
                        effort=pb.effort,
                        steps=pb.steps,
                        references=pb.references,
                        auto_remediable=pb.auto_remediable,
                        automation_script=pb.automation_script,
                    )
                )
            else:
                # Synthesise a basic recommendation from the finding itself
                f = group_findings[0]
                recs.append(
                    Recommendation(
                        id=str(uuid.uuid4()),
                        finding_ids=[f.id],
                        title=f"Remediate: {f.title}",
                        description=(
                            f"Address the following finding on resource `{f.resource_id}`: "
                            f"{f.description}"
                        ),
                        priority=priority,
                        effort="medium",
                        steps=[
                            f"Review and remediate: {f.description}",
                            "Verify the fix by re-scanning the resource.",
                            "Update your IaC templates to prevent recurrence.",
                        ],
                        references=[],
                    )
                )

        return recs

    @staticmethod
    def _find_playbook(text: str) -> Optional[RemediationPlaybook]:
        """Find the most relevant playbook for *text* by keyword matching."""
        text_lower = text.lower()
        best: Optional[RemediationPlaybook] = None
        best_score = 0

        for keyword, pbs in _KEYWORD_INDEX.items():
            if keyword in text_lower:
                # Longer keywords are more specific → prefer them
                score = len(keyword)
                if score > best_score:
                    best_score = score
                    best = pbs[0]

        return best
