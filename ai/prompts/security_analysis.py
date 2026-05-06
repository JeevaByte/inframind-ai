"""
Security analysis prompts and logic for InfraMind AI.

This module provides:
- Security-focused prompt templates (threat modelling, CVE analysis,
  compliance checks, secrets detection, network exposure mapping)
- A ``SecurityAnalysisPromptBuilder`` that assembles complete prompt strings
- A ``SecurityAnalysisLogic`` helper that applies rule-based pre-screening
  before sending data to the AI, reducing token usage and improving accuracy
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ai.models.schemas import (
    CloudProvider,
    Finding,
    FindingSeverity,
    InfraResource,
    ResourceType,
    RiskScore,
)
from ai.prompts.templates import PromptTemplate, TemplateRegistry, get_registry


# ---------------------------------------------------------------------------
# Security prompt templates
# ---------------------------------------------------------------------------

_SECURITY_BASE_TEMPLATE = PromptTemplate(
    name="security_analysis_base",
    description="General-purpose security analysis prompt.",
    required_variables=["resource_type", "configuration_json"],
    default_variables={"provider": "aws", "region": "unknown", "context": "", "focus_areas": ""},
    template="""
    ## Security Analysis

    Perform a comprehensive **security-only** analysis on the following
    **{resource_type}** resource ({provider}, {region}).

    {% if context %}
    ### Context
    {context}
    {% endif %}

    ### Configuration
    ```json
    {configuration_json}
    ```

    Evaluate:
    1. Authentication & authorisation weaknesses
    2. Encryption deficiencies (at-rest and in-transit)
    3. Network exposure and attack surface
    4. Privilege escalation paths
    5. Logging and audit trail gaps
    6. Known CVE applicability based on software versions
    7. Secrets or credentials embedded in configuration

    {% if focus_areas %}
    ### Focus Areas
    {focus_areas}
    {% endif %}
    """,
)

_THREAT_MODEL_TEMPLATE = PromptTemplate(
    name="security_threat_model",
    description="STRIDE-based threat modelling prompt.",
    required_variables=["architecture_json"],
    default_variables={"context": "", "data_classification": "internal"},
    template="""
    ## STRIDE Threat Model

    Data Classification: **{data_classification}**

    {% if context %}
    ### Background
    {context}
    {% endif %}

    ### Architecture / Resource Set
    ```json
    {architecture_json}
    ```

    Apply the **STRIDE** framework to identify threats:
    - **S**poofing — identity impersonation risks
    - **T**ampering — data or configuration modification risks
    - **R**epudiation — audit and non-repudiation gaps
    - **I**nformation Disclosure — data leakage risks
    - **D**enial of Service — availability threats
    - **E**levation of Privilege — privilege escalation paths

    For each identified threat:
    1. Describe the threat scenario
    2. Identify the affected component(s)
    3. Assign a likelihood (high / medium / low)
    4. Assess the potential impact (high / medium / low)
    5. Recommend mitigations
    """,
)

_CVE_ANALYSIS_TEMPLATE = PromptTemplate(
    name="security_cve_analysis",
    description="CVE and vulnerability analysis prompt.",
    required_variables=["software_inventory_json"],
    default_variables={"context": "", "severity_threshold": "medium"},
    template="""
    ## CVE & Vulnerability Analysis

    Severity Threshold: **{severity_threshold}** and above

    {% if context %}
    ### Context
    {context}
    {% endif %}

    ### Software Inventory
    ```json
    {software_inventory_json}
    ```

    For each software component:
    1. Identify known CVEs at or above the severity threshold
    2. Assess exploitability in the given infrastructure context
    3. Note whether a patch or workaround is available
    4. Prioritise based on CVSSv3 base score and exploitability
    5. Provide upgrade/patch guidance

    Group findings by affected component and sort by CVSS score descending.
    """,
)

_COMPLIANCE_CHECK_TEMPLATE = PromptTemplate(
    name="security_compliance_check",
    description="Compliance gap analysis against selected frameworks.",
    required_variables=["configuration_json", "frameworks"],
    default_variables={"resource_type": "infrastructure", "context": ""},
    template="""
    ## Compliance Gap Analysis

    Resource Type: **{resource_type}**
    Frameworks: **{frameworks}**

    {% if context %}
    ### Context
    {context}
    {% endif %}

    ### Configuration
    ```json
    {configuration_json}
    ```

    For each specified framework, evaluate compliance against its controls:
    - List each control ID and its compliance status (PASS / FAIL / NOT_APPLICABLE)
    - For FAIL controls, describe the gap and provide remediation guidance
    - Assign a severity to each gap (critical / high / medium / low)
    - Provide an overall compliance score per framework (0–100%)

    Focus on actionable gaps only; skip controls that are clearly not applicable.
    """,
)

_NETWORK_EXPOSURE_TEMPLATE = PromptTemplate(
    name="security_network_exposure",
    description="Network exposure and attack surface analysis prompt.",
    required_variables=["network_config_json"],
    default_variables={"provider": "aws", "context": ""},
    template="""
    ## Network Exposure & Attack Surface Analysis

    Provider: **{provider}**

    {% if context %}
    ### Context
    {context}
    {% endif %}

    ### Network Configuration
    ```json
    {network_config_json}
    ```

    Analyse:
    1. **Public exposure**: All resources reachable from the public internet
    2. **Port/service inventory**: Open ports and services on each public endpoint
    3. **Overly permissive rules**: Security groups / ACLs allowing broad access
    4. **Lateral movement risk**: Internal network paths that could enable spreading
    5. **Egress controls**: Missing or weak outbound filtering
    6. **DNS exposure**: Publicly resolvable internal hostnames

    Produce an attack surface map and rank entry points by exploitability.
    """,
)

_SECRETS_DETECTION_TEMPLATE = PromptTemplate(
    name="security_secrets_detection",
    description="Secrets and credential detection prompt.",
    required_variables=["configuration_snippets"],
    default_variables={"context": ""},
    template="""
    ## Secrets & Credential Detection

    {% if context %}
    ### Context
    {context}
    {% endif %}

    ### Configuration Data
    ```
    {configuration_snippets}
    ```

    Scan the provided configuration data for:
    1. Hard-coded passwords, API keys, or tokens
    2. Private keys or certificates embedded in config
    3. Database connection strings with credentials
    4. Cloud provider credentials or IAM keys
    5. Webhook URLs containing sensitive tokens
    6. Environment variable leakage in configuration

    For each detected secret:
    - Identify the type and location
    - Assess the risk of exposure
    - Recommend immediate remediation (rotation + move to secrets manager)

    **IMPORTANT**: Redact any actual secret values in your response.
    """,
)

_INCIDENT_RESPONSE_TEMPLATE = PromptTemplate(
    name="security_incident_response",
    description="Incident response guidance prompt.",
    required_variables=["incident_description", "affected_resources_json"],
    default_variables={"context": "", "severity": "high"},
    template="""
    ## Incident Response Guidance

    Severity: **{severity}**

    {% if context %}
    ### Context
    {context}
    {% endif %}

    ### Incident Description
    {incident_description}

    ### Affected Resources
    ```json
    {affected_resources_json}
    ```

    Provide a structured incident response plan:

    **Immediate Actions (0–1 hour)**
    - Containment steps to limit further damage
    - Evidence preservation actions

    **Short-term Actions (1–24 hours)**
    - Root cause investigation steps
    - Notification requirements (internal / regulatory)

    **Remediation (24–72 hours)**
    - Step-by-step remediation guidance
    - Validation / verification steps

    **Post-Incident**
    - Lessons learned recommendations
    - Control improvements to prevent recurrence
    """,
)


# ---------------------------------------------------------------------------
# Register security templates
# ---------------------------------------------------------------------------

_SECURITY_TEMPLATES = [
    _SECURITY_BASE_TEMPLATE,
    _THREAT_MODEL_TEMPLATE,
    _CVE_ANALYSIS_TEMPLATE,
    _COMPLIANCE_CHECK_TEMPLATE,
    _NETWORK_EXPOSURE_TEMPLATE,
    _SECRETS_DETECTION_TEMPLATE,
    _INCIDENT_RESPONSE_TEMPLATE,
]

_registry = get_registry()
for _t in _SECURITY_TEMPLATES:
    _registry.register(_t)


# ---------------------------------------------------------------------------
# Rule-based pre-screening
# ---------------------------------------------------------------------------

# Patterns that indicate a potential secret or credential in a string value
_SECRET_PATTERNS: List[Tuple[str, str]] = [
    (r"(?i)(password|passwd|pwd)\s*[:=]\s*\S+", "password"),
    (r"(?i)(api[_-]?key|apikey)\s*[:=]\s*\S+", "api_key"),
    (r"(?i)(secret[_-]?key|secret)\s*[:=]\s*\S+", "secret"),
    (r"(?i)(access[_-]?key[_-]?id)\s*[:=]\s*\S+", "aws_access_key_id"),
    (r"(?i)(aws[_-]?secret)\s*[:=]\s*\S+", "aws_secret"),
    (r"-----BEGIN (RSA |EC )?PRIVATE KEY-----", "private_key"),
    (r"(?i)(token)\s*[:=]\s*[A-Za-z0-9+/]{20,}", "token"),
    (r"mongodb(\+srv)?://[^:]+:[^@]+@", "mongodb_connection_string"),
    (r"postgres://[^:]+:[^@]+@", "postgres_connection_string"),
]

# Ports considered sensitive when exposed to 0.0.0.0/0
_SENSITIVE_PORTS = {22, 3389, 5432, 3306, 27017, 6379, 9200, 2379, 8080}

# Maximum acceptable CIDR prefix length for "restricted" rule
_MAX_CIDR_PREFIX = 8  # /8 or more specific is considered restricted


@dataclass
class PreScreenResult:
    """Results of the rule-based pre-screening pass."""

    resource_id: str
    suspected_secrets: List[Dict[str, str]] = field(default_factory=list)
    open_sensitive_ports: List[int] = field(default_factory=list)
    has_public_access: bool = False
    encryption_disabled: bool = False
    logging_disabled: bool = False
    pre_findings: List[Finding] = field(default_factory=list)


class SecurityAnalysisLogic:
    """
    Rule-based pre-screening engine.

    Applies deterministic checks to infrastructure resources *before* sending
    data to the AI model.  This has two benefits:
    1. Critical issues are always caught, regardless of LLM output quality.
    2. Reduces token usage by annotating the prompt with known issues.
    """

    def pre_screen(self, resource: InfraResource) -> PreScreenResult:
        """Run all pre-screening rules against *resource*."""
        result = PreScreenResult(resource_id=resource.id)
        config_str = json.dumps(resource.configuration)

        self._check_secrets(resource, config_str, result)
        self._check_public_access(resource, result)
        self._check_encryption(resource, result)
        self._check_logging(resource, result)
        self._check_open_ports(resource, result)

        return result

    # ------------------------------------------------------------------
    # Rule implementations
    # ------------------------------------------------------------------

    def _check_secrets(
        self, resource: InfraResource, config_str: str, result: PreScreenResult
    ) -> None:
        for pattern, secret_type in _SECRET_PATTERNS:
            if re.search(pattern, config_str):
                result.suspected_secrets.append({"type": secret_type, "pattern": pattern})
                result.pre_findings.append(
                    Finding(
                        id=f"PRE-{resource.id}-secret-{secret_type}",
                        resource_id=resource.id,
                        title=f"Potential {secret_type.replace('_', ' ').title()} Detected",
                        description=(
                            f"A pattern matching a {secret_type} was found in the resource "
                            "configuration. Hard-coded credentials are a critical security risk."
                        ),
                        severity=FindingSeverity.CRITICAL,
                        risk_score=RiskScore(
                            base_score=9.0,
                            exploitability=0.9,
                            impact=1.0,
                            rationale="Hard-coded secrets are trivially exploitable and have high impact.",
                        ),
                        affected_attribute="configuration",
                    )
                )

    def _check_public_access(
        self, resource: InfraResource, result: PreScreenResult
    ) -> None:
        config = resource.configuration
        # S3 / storage public access
        if resource.resource_type == ResourceType.STORAGE:
            block_settings = config.get("PublicAccessBlockConfiguration", {})
            if not all(block_settings.get(k, False) for k in [
                "BlockPublicAcls",
                "IgnorePublicAcls",
                "BlockPublicPolicy",
                "RestrictPublicBuckets",
            ]):
                result.has_public_access = True
                result.pre_findings.append(
                    Finding(
                        id=f"PRE-{resource.id}-public-access",
                        resource_id=resource.id,
                        title="Storage Resource Publicly Accessible",
                        description=(
                            "Public Access Block settings are not fully enabled. "
                            "The storage resource may be accessible to the public internet."
                        ),
                        severity=FindingSeverity.HIGH,
                        risk_score=RiskScore(
                            base_score=8.5,
                            exploitability=0.95,
                            impact=0.9,
                            rationale="Publicly accessible storage can lead to data exfiltration.",
                        ),
                        affected_attribute="PublicAccessBlockConfiguration",
                        compliance_frameworks=["CIS AWS 2.1.1", "SOC2 CC6.1"],
                    )
                )

        # Compute / network: check for 0.0.0.0/0 ingress
        if resource.resource_type in (ResourceType.COMPUTE, ResourceType.NETWORK):
            sg_rules = config.get("SecurityGroups", [])
            for sg in sg_rules:
                for perm in sg.get("IpPermissions", []):
                    for ip_range in perm.get("IpRanges", []):
                        if ip_range.get("CidrIp") == "0.0.0.0/0":
                            result.has_public_access = True

    def _check_encryption(
        self, resource: InfraResource, result: PreScreenResult
    ) -> None:
        config = resource.configuration
        disabled = False

        if resource.resource_type == ResourceType.STORAGE:
            sse = config.get("ServerSideEncryptionConfiguration", {})
            rules = sse.get("Rules", [])
            disabled = len(rules) == 0

        elif resource.resource_type == ResourceType.DATABASE:
            disabled = not config.get("StorageEncrypted", True)

        elif resource.resource_type == ResourceType.COMPUTE:
            block_devices = config.get("BlockDeviceMappings", [])
            for bd in block_devices:
                ebs = bd.get("Ebs", {})
                if not ebs.get("Encrypted", True):
                    disabled = True
                    break

        if disabled:
            result.encryption_disabled = True
            result.pre_findings.append(
                Finding(
                    id=f"PRE-{resource.id}-encryption",
                    resource_id=resource.id,
                    title="Encryption at Rest Disabled",
                    description=(
                        "The resource does not have encryption at rest enabled. "
                        "Data stored unencrypted is at risk if storage media is compromised."
                    ),
                    severity=FindingSeverity.HIGH,
                    risk_score=RiskScore(
                        base_score=7.5,
                        exploitability=0.5,
                        impact=0.9,
                        rationale="Unencrypted data is recoverable from storage media.",
                    ),
                    affected_attribute="encryption",
                    compliance_frameworks=["CIS", "PCI-DSS 3.4", "HIPAA 164.312(a)(2)(iv)"],
                )
            )

    def _check_logging(
        self, resource: InfraResource, result: PreScreenResult
    ) -> None:
        config = resource.configuration
        logging_disabled = False

        if resource.resource_type == ResourceType.STORAGE:
            logging_disabled = not config.get("LoggingEnabled", {}).get("TargetBucket")
        elif resource.resource_type == ResourceType.DATABASE:
            logging_disabled = not config.get("EnabledCloudwatchLogsExports")
        elif resource.resource_type == ResourceType.COMPUTE:
            logging_disabled = not config.get("Monitoring", {}).get("State") == "enabled"

        if logging_disabled:
            result.logging_disabled = True
            result.pre_findings.append(
                Finding(
                    id=f"PRE-{resource.id}-logging",
                    resource_id=resource.id,
                    title="Access Logging Disabled",
                    description=(
                        "Access logging or monitoring is not enabled for this resource. "
                        "Without logs, security incidents cannot be detected or investigated."
                    ),
                    severity=FindingSeverity.MEDIUM,
                    risk_score=RiskScore(
                        base_score=5.5,
                        exploitability=0.3,
                        impact=0.7,
                        rationale="Missing logs impair incident detection and forensics.",
                    ),
                    affected_attribute="logging",
                    compliance_frameworks=["CIS", "SOC2 CC7.2", "PCI-DSS 10.1"],
                )
            )

    def _check_open_ports(
        self, resource: InfraResource, result: PreScreenResult
    ) -> None:
        config = resource.configuration
        for sg in config.get("SecurityGroups", []):
            for perm in sg.get("IpPermissions", []):
                from_port = perm.get("FromPort")
                to_port = perm.get("ToPort")
                if from_port is None or to_port is None:
                    continue
                for sensitive_port in _SENSITIVE_PORTS:
                    if from_port <= sensitive_port <= to_port:
                        for ip_range in perm.get("IpRanges", []):
                            cidr = ip_range.get("CidrIp", "")
                            if cidr == "0.0.0.0/0":
                                result.open_sensitive_ports.append(sensitive_port)


# ---------------------------------------------------------------------------
# SecurityAnalysisPromptBuilder
# ---------------------------------------------------------------------------


class SecurityAnalysisPromptBuilder:
    """
    Builds security-focused analysis prompts.

    Usage::

        builder = SecurityAnalysisPromptBuilder()
        prompt = builder.build_security_analysis(resource)
        threat_prompt = builder.build_threat_model(resources)
        compliance_prompt = builder.build_compliance_check(
            resource, frameworks=["CIS", "SOC2", "PCI-DSS"]
        )
    """

    def __init__(self, registry: Optional[TemplateRegistry] = None) -> None:
        self._registry = registry or get_registry()
        self._logic = SecurityAnalysisLogic()

    def build_security_analysis(
        self,
        resource: InfraResource,
        focus_areas: Optional[List[str]] = None,
        extra_context: str = "",
        include_pre_screen_annotation: bool = True,
    ) -> str:
        """Build a security analysis prompt for a single resource."""
        pre_screen = self._logic.pre_screen(resource)
        annotation = ""
        if include_pre_screen_annotation and pre_screen.pre_findings:
            annotation = self._format_pre_screen_annotation(pre_screen)

        variables: Dict[str, Any] = {
            "resource_type": resource.resource_type.value,
            "provider": resource.provider.value,
            "region": resource.region or "unknown",
            "configuration_json": json.dumps(resource.configuration, indent=2),
            "context": f"{extra_context}\n\n{annotation}".strip() if annotation else extra_context,
            "focus_areas": ", ".join(focus_areas) if focus_areas else "",
        }

        system_prompt = self._registry.render("system_context")
        analysis_prompt = self._registry.render("security_analysis_base", variables)
        format_instructions = self._registry.render("json_format_instructions")

        return "\n\n".join([system_prompt, analysis_prompt, format_instructions])

    def build_threat_model(
        self,
        resources: List[InfraResource],
        data_classification: str = "internal",
        extra_context: str = "",
    ) -> str:
        """Build a STRIDE threat model prompt for a set of resources."""
        architecture_json = json.dumps(
            [{"id": r.id, "name": r.name, "type": r.resource_type.value,
              "configuration": r.configuration} for r in resources],
            indent=2,
        )
        variables: Dict[str, Any] = {
            "architecture_json": architecture_json,
            "data_classification": data_classification,
            "context": extra_context,
        }
        system_prompt = self._registry.render("system_context")
        threat_prompt = self._registry.render("security_threat_model", variables)
        format_instructions = self._registry.render("json_format_instructions")
        return "\n\n".join([system_prompt, threat_prompt, format_instructions])

    def build_compliance_check(
        self,
        resource: InfraResource,
        frameworks: Optional[List[str]] = None,
        extra_context: str = "",
    ) -> str:
        """Build a compliance gap analysis prompt."""
        frameworks = frameworks or ["CIS", "SOC2", "PCI-DSS"]
        variables: Dict[str, Any] = {
            "resource_type": resource.resource_type.value,
            "configuration_json": json.dumps(resource.configuration, indent=2),
            "frameworks": ", ".join(frameworks),
            "context": extra_context,
        }
        system_prompt = self._registry.render("system_context")
        compliance_prompt = self._registry.render("security_compliance_check", variables)
        format_instructions = self._registry.render("json_format_instructions")
        return "\n\n".join([system_prompt, compliance_prompt, format_instructions])

    def build_network_exposure_analysis(
        self,
        network_resources: List[InfraResource],
        provider: CloudProvider = CloudProvider.AWS,
        extra_context: str = "",
    ) -> str:
        """Build a network exposure analysis prompt."""
        network_config = json.dumps(
            [{"id": r.id, "name": r.name, "configuration": r.configuration}
             for r in network_resources],
            indent=2,
        )
        variables: Dict[str, Any] = {
            "network_config_json": network_config,
            "provider": provider.value,
            "context": extra_context,
        }
        system_prompt = self._registry.render("system_context")
        network_prompt = self._registry.render("security_network_exposure", variables)
        format_instructions = self._registry.render("json_format_instructions")
        return "\n\n".join([system_prompt, network_prompt, format_instructions])

    def build_cve_analysis(
        self,
        software_inventory: List[Dict[str, str]],
        severity_threshold: str = "medium",
        extra_context: str = "",
    ) -> str:
        """Build a CVE analysis prompt from a software inventory list."""
        variables: Dict[str, Any] = {
            "software_inventory_json": json.dumps(software_inventory, indent=2),
            "severity_threshold": severity_threshold,
            "context": extra_context,
        }
        system_prompt = self._registry.render("system_context")
        cve_prompt = self._registry.render("security_cve_analysis", variables)
        format_instructions = self._registry.render("json_format_instructions")
        return "\n\n".join([system_prompt, cve_prompt, format_instructions])

    def build_incident_response(
        self,
        incident_description: str,
        affected_resources: List[InfraResource],
        severity: str = "high",
        extra_context: str = "",
    ) -> str:
        """Build an incident response guidance prompt."""
        variables: Dict[str, Any] = {
            "incident_description": incident_description,
            "affected_resources_json": json.dumps(
                [{"id": r.id, "name": r.name, "type": r.resource_type.value} for r in affected_resources],
                indent=2,
            ),
            "severity": severity,
            "context": extra_context,
        }
        system_prompt = self._registry.render("system_context")
        ir_prompt = self._registry.render("security_incident_response", variables)
        return "\n\n".join([system_prompt, ir_prompt])

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _format_pre_screen_annotation(pre_screen: PreScreenResult) -> str:
        lines = ["### Pre-Screen Findings (rule-based, apply before AI analysis)"]
        for finding in pre_screen.pre_findings:
            lines.append(
                f"- [{finding.severity.value.upper()}] {finding.title}: {finding.description}"
            )
        return "\n".join(lines)
