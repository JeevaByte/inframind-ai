from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

import yaml

from app.models.common import InfraFileType, Severity


@dataclass
class ParsedSignal:
    title: str
    category: str
    severity: str
    description: str
    recommendation: str
    estimated_impact: str = ""
    resource: str | None = None
    line_number: int | None = None


@dataclass
class ParsedInfrastructureContext:
    file_name: str
    file_type: InfraFileType
    providers: List[str] = field(default_factory=list)
    resources: List[Dict[str, Any]] = field(default_factory=list)
    signals: List[ParsedSignal] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    raw_excerpt: str = ""

    def to_prompt_dict(self) -> Dict[str, Any]:
        return {
            "file_name": self.file_name,
            "file_type": self.file_type.value,
            "providers": self.providers,
            "resources": self.resources,
            "signals": [asdict(signal) for signal in self.signals],
            "summary": self.summary,
            "raw_excerpt": self.raw_excerpt,
        }


_SECRET_PATTERN = re.compile(r"(password|secret|token|api[_-]?key|access[_-]?key)\s*[:=]\s*[\"']?[^\s\"']+", re.IGNORECASE)
_PUBLIC_PATTERN = re.compile(r"0\.0\.0\.0/0|public-read|public-read-write|LoadBalancer", re.IGNORECASE)
_WILDCARD_IAM_PATTERN = re.compile(r"Action\s*[:=]\s*[\"']\*[\"']|actions\s*=\s*\[[^\]]*\*", re.IGNORECASE)


class InfrastructureParser:
    def parse(self, *, file_name: str, content: str, file_type: InfraFileType, max_excerpt_chars: int) -> ParsedInfrastructureContext:
        parser = {
            InfraFileType.TERRAFORM: self._parse_terraform,
            InfraFileType.KUBERNETES: self._parse_kubernetes,
            InfraFileType.CLOUDFORMATION: self._parse_cloudformation,
            InfraFileType.DOCKERFILE: self._parse_dockerfile,
            InfraFileType.GITHUB_ACTIONS: self._parse_github_actions,
        }.get(file_type, self._parse_generic)

        context = parser(file_name=file_name, content=content)
        context.raw_excerpt = content[:max_excerpt_chars]
        self._append_global_signals(context, content)
        context.summary = {
            "resource_count": len(context.resources),
            "provider_count": len(context.providers),
            "signal_count": len(context.signals),
            "resource_types": sorted({resource.get("type", "unknown") for resource in context.resources}),
        }
        return context

    def _parse_terraform(self, *, file_name: str, content: str) -> ParsedInfrastructureContext:
        providers = re.findall(r'provider\s+"([^"]+)"', content)
        resources = []
        signals: List[ParsedSignal] = []

        for match in re.finditer(r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{', content):
            resource_type, resource_name = match.groups()
            resources.append({"type": resource_type, "name": resource_name, "provider": providers[0] if providers else "unknown"})

        if "cidr_blocks = [\"0.0.0.0/0\"]" in content or "0.0.0.0/0" in content:
            signals.append(self._signal("Public ingress exposed", "security", Severity.HIGH, "Network rules allow unrestricted inbound access from the public internet.", "Restrict ingress rules to trusted CIDR ranges or move the workload behind a private endpoint.", "High risk of external attack surface expansion."))
        if _WILDCARD_IAM_PATTERN.search(content):
            signals.append(self._signal("Wildcard IAM permissions detected", "security", Severity.CRITICAL, "IAM configuration contains wildcard permissions that violate least privilege.", "Scope actions and resources to the smallest set required by the workload.", "Credential misuse could lead to full account compromise."))
        if "encrypted = false" in content or "kms_key_id" not in content and "aws_s3_bucket" in content:
            signals.append(self._signal("Encryption posture is weak", "security", Severity.HIGH, "One or more Terraform resources appear to lack encryption-at-rest safeguards.", "Enable encryption for storage, databases, and stateful services using provider-managed or customer-managed keys.", "Unencrypted data increases breach and compliance risk."))
        if "tags = {}" in content or (resources and "tags" not in content):
            signals.append(self._signal("Resource tagging is incomplete", "compliance", Severity.MEDIUM, "Resources are missing ownership or environment tags needed for governance and cost allocation.", "Add Owner, Environment, and CostCenter style tags consistently across resources.", "Weak governance slows incident response and cost attribution."))
        if re.search(r'instance_type\s*=\s*"(m5\.4xlarge|m6i\.8xlarge|c5\.9xlarge|r5\.8xlarge|p3\.|p4\.)', content):
            signals.append(self._signal("Large compute instance detected", "cost", Severity.MEDIUM, "Terraform provisions a high-cost instance size that may be oversized for a demo or steady-state workload.", "Validate utilization data and downsize or autoscale where possible.", "Potential ongoing cloud cost waste."))

        return ParsedInfrastructureContext(file_name=file_name, file_type=InfraFileType.TERRAFORM, providers=sorted(set(providers)), resources=resources, signals=signals)

    def _parse_kubernetes(self, *, file_name: str, content: str) -> ParsedInfrastructureContext:
        resources: List[Dict[str, Any]] = []
        signals: List[ParsedSignal] = []
        docs = [doc for doc in yaml.safe_load_all(content) if isinstance(doc, dict)]

        for doc in docs:
            kind = str(doc.get("kind", "Unknown"))
            metadata = doc.get("metadata") or {}
            spec = doc.get("spec") or {}
            resources.append({"type": kind.lower(), "name": metadata.get("name", kind.lower()), "namespace": metadata.get("namespace", "default")})

            containers = self._extract_k8s_containers(spec)
            for container in containers:
                if not container.get("resources"):
                    signals.append(self._signal("Container missing resource requests and limits", "reliability", Severity.MEDIUM, f"Container {container.get('name', 'unknown')} does not define requests or limits.", "Set CPU and memory requests/limits to improve scheduling stability and cost control.", "Workload can become noisy or hard to autoscale."))
                if not container.get("livenessProbe") or not container.get("readinessProbe"):
                    signals.append(self._signal("Health probes are missing", "reliability", Severity.HIGH, f"Container {container.get('name', 'unknown')} is missing liveness or readiness probes.", "Add both readiness and liveness probes so Kubernetes can route and recover traffic correctly.", "Deployment failures and brownouts become harder to recover from."))
                security_context = container.get("securityContext") or {}
                if security_context.get("privileged") is True:
                    signals.append(self._signal("Privileged container detected", "security", Severity.CRITICAL, f"Container {container.get('name', 'unknown')} is configured as privileged.", "Drop privileged mode and use the minimum Linux capabilities required.", "Container breakout impact becomes severe."))
                if security_context.get("runAsUser") == 0:
                    signals.append(self._signal("Container runs as root", "security", Severity.HIGH, f"Container {container.get('name', 'unknown')} is configured to run as UID 0.", "Run as a non-root user and set a restricted security context.", "Compromise impact inside the container increases significantly."))

            if kind.lower() == "service" and str(spec.get("type", "")).lower() == "loadbalancer":
                signals.append(self._signal("Public service exposure detected", "security", Severity.HIGH, "A Kubernetes Service of type LoadBalancer exposes the workload publicly.", "Restrict ingress, use an internal load balancer, or place the service behind authenticated ingress.", "The workload may be directly reachable from the internet."))

        return ParsedInfrastructureContext(file_name=file_name, file_type=InfraFileType.KUBERNETES, resources=resources, signals=signals)

    def _parse_cloudformation(self, *, file_name: str, content: str) -> ParsedInfrastructureContext:
        resources: List[Dict[str, Any]] = []
        signals: List[ParsedSignal] = []
        document = self._safe_load_structured(content)
        provider = "aws"

        resources_map = document.get("Resources") if isinstance(document, dict) else {}
        if isinstance(resources_map, dict):
            for logical_id, definition in resources_map.items():
                resource_type = definition.get("Type", "Unknown") if isinstance(definition, dict) else "Unknown"
                resources.append({"type": resource_type, "name": logical_id, "provider": provider})

        text = content
        if "0.0.0.0/0" in text:
            signals.append(self._signal("Public network access detected", "security", Severity.HIGH, "CloudFormation networking rules permit unrestricted public access.", "Narrow CIDR ranges or move the resource into private networking.", "Internet exposure increases external attack surface."))
        if "PublicRead" in text or "PublicAccessBlockConfiguration" not in text and "AWS::S3::Bucket" in text:
            signals.append(self._signal("S3 bucket may be publicly accessible", "security", Severity.HIGH, "CloudFormation defines an S3 bucket without an explicit public access block posture.", "Enable S3 Block Public Access and restrict bucket policies.", "Data exposure risk for object storage."))
        if "BucketEncryption" not in text and "AWS::S3::Bucket" in text:
            signals.append(self._signal("Bucket encryption not configured", "security", Severity.HIGH, "S3 storage is missing an explicit server-side encryption configuration.", "Enable AES256 or KMS-based bucket encryption.", "Unencrypted data increases security and compliance risk."))

        return ParsedInfrastructureContext(file_name=file_name, file_type=InfraFileType.CLOUDFORMATION, providers=[provider], resources=resources, signals=signals)

    def _parse_dockerfile(self, *, file_name: str, content: str) -> ParsedInfrastructureContext:
        resources = [{"type": "docker_image", "name": file_name, "provider": "container"}]
        signals: List[ParsedSignal] = []
        base_images = re.findall(r"^FROM\s+([^\s]+)", content, re.MULTILINE)

        if not re.search(r"^USER\s+", content, re.MULTILINE):
            signals.append(self._signal("Docker image runs as default root user", "security", Severity.HIGH, "The Dockerfile does not switch to a non-root USER.", "Add a dedicated non-root user before the final runtime stage.", "Container compromise impact becomes larger."))
        if ":latest" in content:
            signals.append(self._signal("Unpinned container image tag", "compliance", Severity.MEDIUM, "The Dockerfile references a latest-tagged base image.", "Pin the image to a specific version or digest for reproducibility.", "Builds may drift between deployments."))
        if _SECRET_PATTERN.search(content):
            signals.append(self._signal("Potential hardcoded secret in Dockerfile", "security", Severity.CRITICAL, "Build instructions or environment variables appear to contain credentials or tokens.", "Move secrets to runtime injection or a managed secret store.", "Secret leakage can compromise build or runtime environments."))

        return ParsedInfrastructureContext(file_name=file_name, file_type=InfraFileType.DOCKERFILE, providers=["container"], resources=[{**resources[0], "base_images": base_images}], signals=signals)

    def _parse_github_actions(self, *, file_name: str, content: str) -> ParsedInfrastructureContext:
        resources = [{"type": "github_actions_workflow", "name": file_name, "provider": "github"}]
        signals: List[ParsedSignal] = []
        document = self._safe_load_structured(content)
        jobs = document.get("jobs", {}) if isinstance(document, dict) else {}
        resources[0]["job_count"] = len(jobs) if isinstance(jobs, dict) else 0

        if "permissions:" not in content:
            signals.append(self._signal("Workflow permissions are implicit", "compliance", Severity.MEDIUM, "GitHub Actions workflow does not define explicit token permissions.", "Add a least-privilege permissions block at workflow or job level.", "The default token may have broader access than intended."))
        if re.search(r"uses:\s+.+@(main|master)", content):
            signals.append(self._signal("Unpinned GitHub Action reference", "security", Severity.HIGH, "Workflow uses a mutable branch reference such as main or master.", "Pin actions to a full commit SHA or a trusted immutable version tag.", "Supply-chain risk increases when referenced actions change unexpectedly."))
        if _SECRET_PATTERN.search(content):
            signals.append(self._signal("Potential secret committed to workflow", "security", Severity.CRITICAL, "Workflow content appears to include a hardcoded credential-like value.", "Reference secrets through the GitHub Actions secrets store instead of inline values.", "Credential exposure can compromise CI/CD and cloud credentials."))

        return ParsedInfrastructureContext(file_name=file_name, file_type=InfraFileType.GITHUB_ACTIONS, providers=["github"], resources=resources, signals=signals)

    def _parse_generic(self, *, file_name: str, content: str) -> ParsedInfrastructureContext:
        return ParsedInfrastructureContext(file_name=file_name, file_type=InfraFileType.UNKNOWN)

    def _extract_k8s_containers(self, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        pod_spec = spec.get("template", {}).get("spec") or spec.get("jobTemplate", {}).get("spec", {}).get("template", {}).get("spec") or spec
        containers = pod_spec.get("containers") or []
        return [container for container in containers if isinstance(container, dict)]

    def _append_global_signals(self, context: ParsedInfrastructureContext, content: str) -> None:
        if _SECRET_PATTERN.search(content):
            context.signals.append(self._signal("Potential hardcoded secret detected", "security", Severity.CRITICAL, "The uploaded infrastructure file contains a value that looks like a hardcoded credential or token.", "Replace inline credentials with secret references or environment injection.", "Secrets in source control can lead to direct account compromise."))
        if _PUBLIC_PATTERN.search(content) and not any(signal.title == "Public ingress exposed" for signal in context.signals):
            context.signals.append(self._signal("Public exposure pattern found", "security", Severity.HIGH, "The configuration includes markers commonly associated with public network or storage exposure.", "Review whether the resource must be internet facing and add compensating controls if it is.", "Publicly reachable infrastructure increases exploitability."))

    def _signal(self, title: str, category: str, severity: Severity, description: str, recommendation: str, estimated_impact: str) -> ParsedSignal:
        return ParsedSignal(title=title, category=category, severity=severity.value, description=description, recommendation=recommendation, estimated_impact=estimated_impact)

    def _safe_load_structured(self, content: str) -> Dict[str, Any]:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            data = yaml.safe_load(content)
            return data if isinstance(data, dict) else {}