"""
Infrastructure analysis prompts for InfraMind AI.

This module defines prompt templates and a builder class for generating
AI prompts that analyse cloud infrastructure resources for misconfigurations,
cost optimisation opportunities, and operational best practices.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ai.models.schemas import CloudProvider, InfraResource, ResourceType
from ai.prompts.templates import PromptTemplate, TemplateRegistry, get_registry


# ---------------------------------------------------------------------------
# Prompt templates — infrastructure analysis
# ---------------------------------------------------------------------------

_INFRA_BASE_TEMPLATE = PromptTemplate(
    name="infra_analysis_base",
    description="Base infrastructure analysis prompt.",
    required_variables=["resource_type", "provider", "configuration_json"],
    default_variables={"region": "unknown", "focus_areas": "", "context": ""},
    template="""
    ## Infrastructure Resource Analysis

    Analyse the following **{resource_type}** resource hosted on **{provider}**
    (region: {region}).

    {% if context %}
    ### Additional Context
    {context}
    {% endif %}

    ### Configuration Snapshot
    ```json
    {configuration_json}
    ```

    ### Analysis Instructions
    1. Identify all security misconfigurations (authentication, authorisation, encryption,
       network exposure, logging, monitoring).
    2. Check for compliance gaps against CIS Benchmarks, SOC 2, and PCI-DSS where applicable.
    3. Highlight operational concerns (availability, scalability, backup/recovery, cost).
    4. Score each finding using CVSS-aligned methodology (base_score 0–10,
       exploitability 0–1, impact 0–1).
    5. Provide step-by-step remediation guidance for every finding.

    {% if focus_areas %}
    ### Focus Areas
    Prioritise these areas in your analysis: {focus_areas}.
    {% endif %}
    """,
)

_COMPUTE_TEMPLATE = PromptTemplate(
    name="infra_analysis_compute",
    description="Compute-specific analysis prompt (EC2, GCE, VMs).",
    required_variables=["configuration_json"],
    default_variables={"provider": "aws", "region": "unknown", "focus_areas": "", "context": ""},
    template="""
    ## Compute Resource Security & Configuration Analysis

    Provider: **{provider}** | Region: **{region}**

    {% if context %}
    ### Context
    {context}
    {% endif %}

    ### Instance Configuration
    ```json
    {configuration_json}
    ```

    ### Checklist
    - [ ] IMDSv2 enforced (AWS) / metadata server access controls
    - [ ] Security groups / firewall rules — no 0.0.0.0/0 on sensitive ports
    - [ ] SSH/RDP access restricted to known CIDR ranges
    - [ ] Root / admin account usage disabled
    - [ ] EBS/disk encryption at rest
    - [ ] Auto-patching or patch management policy in place
    - [ ] Instance in a private subnet (public IP only where required)
    - [ ] CloudWatch / Stackdriver monitoring and alerting configured
    - [ ] IAM instance profile with least-privilege permissions
    - [ ] User-data / startup scripts reviewed for secrets

    Analyse each checklist item and report findings with severity and remediation steps.

    {% if focus_areas %}
    Focus particularly on: {focus_areas}
    {% endif %}
    """,
)

_STORAGE_TEMPLATE = PromptTemplate(
    name="infra_analysis_storage",
    description="Storage-specific analysis prompt (S3, GCS, Azure Blob).",
    required_variables=["configuration_json"],
    default_variables={"provider": "aws", "region": "unknown", "focus_areas": "", "context": ""},
    template="""
    ## Storage Resource Security & Configuration Analysis

    Provider: **{provider}** | Region: **{region}**

    {% if context %}
    ### Context
    {context}
    {% endif %}

    ### Resource Configuration
    ```json
    {configuration_json}
    ```

    ### Checklist
    - [ ] Bucket / container is NOT publicly accessible
    - [ ] Block Public Access settings enabled (AWS S3)
    - [ ] Server-side encryption enabled (AES-256 or KMS)
    - [ ] Versioning enabled for critical data
    - [ ] Object-level logging / access logs enabled
    - [ ] Lifecycle policies configured to prevent unbounded data accumulation
    - [ ] Cross-region replication configured for DR requirements
    - [ ] Bucket policy / ACLs reviewed — principle of least privilege
    - [ ] No wildcard (*) principals in bucket policies
    - [ ] MFA Delete enabled for production buckets

    Analyse each checklist item and report findings with severity and remediation steps.

    {% if focus_areas %}
    Focus particularly on: {focus_areas}
    {% endif %}
    """,
)

_NETWORK_TEMPLATE = PromptTemplate(
    name="infra_analysis_network",
    description="Network-specific analysis prompt (VPCs, subnets, security groups, firewalls).",
    required_variables=["configuration_json"],
    default_variables={"provider": "aws", "region": "unknown", "focus_areas": "", "context": ""},
    template="""
    ## Network Infrastructure Analysis

    Provider: **{provider}** | Region: **{region}**

    {% if context %}
    ### Context
    {context}
    {% endif %}

    ### Network Configuration
    ```json
    {configuration_json}
    ```

    ### Checklist
    - [ ] VPC / network segmentation in place (public vs. private subnets)
    - [ ] Default VPC not used for production workloads
    - [ ] Security groups / NACLs follow least-privilege ingress/egress
    - [ ] No overly permissive rules (0.0.0.0/0 on sensitive ports)
    - [ ] VPC Flow Logs enabled
    - [ ] DNS resolution and hostnames configured appropriately
    - [ ] NAT Gateway used for outbound internet access from private subnets
    - [ ] Peering connections / Transit Gateway permissions scoped correctly
    - [ ] WAF configured for public-facing load balancers
    - [ ] DDoS protection (AWS Shield / Cloud Armor) in place

    Analyse each checklist item and report findings with severity and remediation steps.

    {% if focus_areas %}
    Focus particularly on: {focus_areas}
    {% endif %}
    """,
)

_DATABASE_TEMPLATE = PromptTemplate(
    name="infra_analysis_database",
    description="Database-specific analysis prompt (RDS, Cloud SQL, Cosmos DB).",
    required_variables=["configuration_json"],
    default_variables={"provider": "aws", "region": "unknown", "focus_areas": "", "context": ""},
    template="""
    ## Database Resource Security & Configuration Analysis

    Provider: **{provider}** | Region: **{region}**

    {% if context %}
    ### Context
    {context}
    {% endif %}

    ### Database Configuration
    ```json
    {configuration_json}
    ```

    ### Checklist
    - [ ] Database NOT publicly accessible
    - [ ] Encryption at rest enabled (KMS / Cloud KMS)
    - [ ] Encryption in transit enforced (SSL/TLS required)
    - [ ] Automated backups enabled with appropriate retention period
    - [ ] Multi-AZ / high-availability mode configured
    - [ ] Database activity monitoring / audit logs enabled
    - [ ] Default admin credentials changed
    - [ ] Database minor version auto-upgrade enabled
    - [ ] VPC security group restricts access to application tier only
    - [ ] Parameter group hardening applied (disable unsafe functions)

    Analyse each checklist item and report findings with severity and remediation steps.

    {% if focus_areas %}
    Focus particularly on: {focus_areas}
    {% endif %}
    """,
)

_IAM_TEMPLATE = PromptTemplate(
    name="infra_analysis_iam",
    description="IAM / identity-specific analysis prompt.",
    required_variables=["configuration_json"],
    default_variables={"provider": "aws", "region": "N/A", "focus_areas": "", "context": ""},
    template="""
    ## IAM & Identity Configuration Analysis

    Provider: **{provider}**

    {% if context %}
    ### Context
    {context}
    {% endif %}

    ### IAM Configuration
    ```json
    {configuration_json}
    ```

    ### Checklist
    - [ ] Root / admin account has MFA enabled
    - [ ] No long-lived access keys for root account
    - [ ] Access keys rotated within 90 days
    - [ ] Users / service accounts follow least-privilege principle
    - [ ] No wildcard (*) actions or resources in custom policies
    - [ ] IAM roles used instead of IAM users for service-to-service auth
    - [ ] Unused IAM entities (users, roles, policies) removed
    - [ ] Password policy enforces complexity, length, and rotation
    - [ ] MFA enforced for all human users with console access
    - [ ] CloudTrail / Audit Logs enabled and monitoring IAM changes

    Analyse each checklist item and report findings with severity and remediation steps.

    {% if focus_areas %}
    Focus particularly on: {focus_areas}
    {% endif %}
    """,
)

_CONTAINER_TEMPLATE = PromptTemplate(
    name="infra_analysis_container",
    description="Container / Kubernetes analysis prompt (EKS, GKE, AKS, ECS).",
    required_variables=["configuration_json"],
    default_variables={"provider": "aws", "region": "unknown", "focus_areas": "", "context": ""},
    template="""
    ## Container & Orchestration Security Analysis

    Provider: **{provider}** | Region: **{region}**

    {% if context %}
    ### Context
    {context}
    {% endif %}

    ### Cluster / Container Configuration
    ```json
    {configuration_json}
    ```

    ### Checklist
    - [ ] Kubernetes API server NOT publicly accessible
    - [ ] RBAC configured with least-privilege roles and bindings
    - [ ] Pod Security Admission / PodSecurityPolicy in place
    - [ ] Network policies restrict pod-to-pod communication
    - [ ] Secrets stored in dedicated secret manager (not plain ConfigMaps)
    - [ ] Container images scanned for vulnerabilities before deployment
    - [ ] Containers run as non-root user
    - [ ] Resource limits (CPU / memory) defined for all workloads
    - [ ] Namespaces used for workload isolation
    - [ ] Cluster autoscaler and node group configurations reviewed

    Analyse each checklist item and report findings with severity and remediation steps.

    {% if focus_areas %}
    Focus particularly on: {focus_areas}
    {% endif %}
    """,
)

_MULTI_RESOURCE_TEMPLATE = PromptTemplate(
    name="infra_analysis_multi_resource",
    description="Multi-resource holistic infrastructure analysis prompt.",
    required_variables=["resources_json"],
    default_variables={"provider": "aws", "context": "", "focus_areas": ""},
    template="""
    ## Holistic Infrastructure Analysis

    Provider: **{provider}**

    {% if context %}
    ### Environment Context
    {context}
    {% endif %}

    ### Resources Under Analysis
    ```json
    {resources_json}
    ```

    ### Analysis Instructions
    Perform a **holistic** analysis of the entire infrastructure set:

    1. **Cross-resource risks**: Identify issues that span multiple resources
       (e.g. overly permissive IAM role granting access to a public S3 bucket).
    2. **Attack surface mapping**: Enumerate publicly accessible entry points and
       the blast radius of a compromise.
    3. **Lateral movement paths**: Identify trust relationships that could allow
       an attacker to move between resources.
    4. **Compliance coverage**: Assess overall compliance posture across the
       resource set.
    5. **Resource-level findings**: Individual findings for each resource.

    {% if focus_areas %}
    ### Focus Areas
    {focus_areas}
    {% endif %}
    """,
)

_SUMMARY_TEMPLATE = PromptTemplate(
    name="infra_analysis_summary",
    description="Executive summary generation prompt.",
    required_variables=["findings_json"],
    default_variables={"environment": "production", "context": ""},
    template="""
    ## Executive Summary Generation

    Environment: **{environment}**

    {% if context %}
    ### Background
    {context}
    {% endif %}

    ### Findings Data
    ```json
    {findings_json}
    ```

    Generate a concise executive summary (3–5 paragraphs) covering:
    1. Overall security and compliance posture
    2. Most critical findings and their business impact
    3. Recommended immediate actions
    4. Trend observations (if prior data is available)
    5. Overall risk rating (Critical / High / Medium / Low)

    The summary should be suitable for a non-technical audience.
    """,
)


# ---------------------------------------------------------------------------
# Register templates
# ---------------------------------------------------------------------------

_INFRA_TEMPLATES = [
    _INFRA_BASE_TEMPLATE,
    _COMPUTE_TEMPLATE,
    _STORAGE_TEMPLATE,
    _NETWORK_TEMPLATE,
    _DATABASE_TEMPLATE,
    _IAM_TEMPLATE,
    _CONTAINER_TEMPLATE,
    _MULTI_RESOURCE_TEMPLATE,
    _SUMMARY_TEMPLATE,
]

_registry = get_registry()
for _t in _INFRA_TEMPLATES:
    _registry.register(_t)


# ---------------------------------------------------------------------------
# ResourceType → template name mapping
# ---------------------------------------------------------------------------

_RESOURCE_TYPE_TEMPLATE_MAP: Dict[ResourceType, str] = {
    ResourceType.COMPUTE: "infra_analysis_compute",
    ResourceType.STORAGE: "infra_analysis_storage",
    ResourceType.NETWORK: "infra_analysis_network",
    ResourceType.DATABASE: "infra_analysis_database",
    ResourceType.IAM: "infra_analysis_iam",
    ResourceType.CONTAINER: "infra_analysis_container",
}


# ---------------------------------------------------------------------------
# InfraAnalysisPromptBuilder
# ---------------------------------------------------------------------------


class InfraAnalysisPromptBuilder:
    """
    Builds analysis prompts for infrastructure resources.

    Usage::

        builder = InfraAnalysisPromptBuilder()
        prompt = builder.build_for_resource(resource, focus_areas=["encryption"])
    """

    def __init__(self, registry: Optional[TemplateRegistry] = None) -> None:
        self._registry = registry or get_registry()

    def build_for_resource(
        self,
        resource: InfraResource,
        focus_areas: Optional[List[str]] = None,
        extra_context: str = "",
    ) -> str:
        """
        Build an analysis prompt for a single infrastructure resource.

        Selects the most specific template available for the resource type,
        falling back to the generic base template.
        """
        import json

        template_name = _RESOURCE_TYPE_TEMPLATE_MAP.get(
            resource.resource_type, "infra_analysis_base"
        )

        variables: Dict[str, Any] = {
            "resource_type": resource.resource_type.value,
            "provider": resource.provider.value,
            "region": resource.region or "unknown",
            "configuration_json": json.dumps(resource.configuration, indent=2),
            "context": extra_context,
            "focus_areas": ", ".join(focus_areas) if focus_areas else "",
        }

        system_prompt = self._registry.render("system_context")
        analysis_prompt = self._registry.render(template_name, variables)
        format_instructions = self._registry.render("json_format_instructions")

        return "\n\n".join([system_prompt, analysis_prompt, format_instructions])

    def build_for_multiple_resources(
        self,
        resources: List[InfraResource],
        focus_areas: Optional[List[str]] = None,
        extra_context: str = "",
        provider: CloudProvider = CloudProvider.AWS,
    ) -> str:
        """
        Build a holistic analysis prompt for multiple infrastructure resources.
        """
        import json

        resources_json = json.dumps(
            [
                {
                    "id": r.id,
                    "name": r.name,
                    "type": r.resource_type.value,
                    "region": r.region,
                    "configuration": r.configuration,
                    "tags": r.tags,
                }
                for r in resources
            ],
            indent=2,
        )

        variables: Dict[str, Any] = {
            "resources_json": resources_json,
            "provider": provider.value,
            "context": extra_context,
            "focus_areas": ", ".join(focus_areas) if focus_areas else "",
        }

        system_prompt = self._registry.render("system_context")
        analysis_prompt = self._registry.render("infra_analysis_multi_resource", variables)
        format_instructions = self._registry.render("json_format_instructions")

        return "\n\n".join([system_prompt, analysis_prompt, format_instructions])

    def build_summary_prompt(
        self,
        findings_json: str,
        environment: str = "production",
        extra_context: str = "",
    ) -> str:
        """Build an executive summary prompt from a JSON findings payload."""
        variables: Dict[str, Any] = {
            "findings_json": findings_json,
            "environment": environment,
            "context": extra_context,
        }
        return self._registry.render("infra_analysis_summary", variables)
