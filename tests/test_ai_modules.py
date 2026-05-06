"""
Comprehensive test suite for InfraMind AI modules.

Tests cover:
- PromptTemplate rendering and registry
- InfraAnalysisPromptBuilder
- SecurityAnalysisPromptBuilder + SecurityAnalysisLogic
- RiskScoringEngine
- ResponseParser + ResponseFormatter
- RecommendationEngine
- AIOrchestrator (end-to-end with MockProvider)
"""

from __future__ import annotations

import json
import uuid

import pytest

from ai.formatting.response_formatter import ResponseFormatter, ResponseParser, _extract_json
from ai.models.schemas import (
    AnalysisRequest,
    AnalysisResult,
    CloudProvider,
    Finding,
    FindingSeverity,
    InfraResource,
    Recommendation,
    RemediationPriority,
    ResourceType,
    RiskScore,
)
from ai.orchestration.orchestrator import (
    AIOrchestrator,
    MockProvider,
    OrchestratorConfig,
)
from ai.prompts.infra_analysis import InfraAnalysisPromptBuilder
from ai.prompts.security_analysis import SecurityAnalysisLogic, SecurityAnalysisPromptBuilder
from ai.prompts.templates import PromptTemplate, TemplateRegistry, get_registry
from ai.recommendation.engine import RecommendationEngine
from ai.risk.scoring import (
    AggregateRiskResult,
    DataSensitivity,
    EnvironmentModifier,
    RiskBand,
    RiskScoringEngine,
    score_to_risk_band,
    severity_from_score,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def s3_resource() -> InfraResource:
    return InfraResource(
        id="bucket-001",
        name="my-data-bucket",
        resource_type=ResourceType.STORAGE,
        provider=CloudProvider.AWS,
        region="us-east-1",
        configuration={
            "BucketName": "my-data-bucket",
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": False,
                "IgnorePublicAcls": False,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            },
            "ServerSideEncryptionConfiguration": {"Rules": []},
            "LoggingEnabled": {},
        },
    )


@pytest.fixture()
def ec2_resource() -> InfraResource:
    return InfraResource(
        id="i-0abc123",
        name="web-server",
        resource_type=ResourceType.COMPUTE,
        provider=CloudProvider.AWS,
        region="us-west-2",
        configuration={
            "InstanceId": "i-0abc123",
            "MetadataOptions": {"HttpTokens": "optional"},
            "SecurityGroups": [
                {
                    "GroupId": "sg-111",
                    "IpPermissions": [
                        {
                            "FromPort": 22,
                            "ToPort": 22,
                            "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                        }
                    ],
                }
            ],
            "BlockDeviceMappings": [{"Ebs": {"Encrypted": False}}],
            "Monitoring": {"State": "disabled"},
        },
    )


@pytest.fixture()
def rds_resource() -> InfraResource:
    return InfraResource(
        id="db-prod-001",
        name="prod-postgres",
        resource_type=ResourceType.DATABASE,
        provider=CloudProvider.AWS,
        region="eu-west-1",
        configuration={
            "DBInstanceIdentifier": "db-prod-001",
            "StorageEncrypted": False,
            "PubliclyAccessible": True,
            "MultiAZ": False,
            "BackupRetentionPeriod": 0,
        },
    )


@pytest.fixture()
def sample_finding(s3_resource: InfraResource) -> Finding:
    return Finding(
        id="F-001",
        resource_id=s3_resource.id,
        title="S3 Bucket Publicly Accessible",
        description="The bucket allows public access.",
        severity=FindingSeverity.HIGH,
        risk_score=RiskScore(base_score=8.0, exploitability=0.9, impact=0.9),
        compliance_frameworks=["CIS AWS 2.1.1"],
    )


@pytest.fixture()
def sample_result(sample_finding: Finding) -> AnalysisResult:
    rec = Recommendation(
        id="R-001",
        finding_ids=["F-001"],
        title="Enable S3 Block Public Access",
        description="Enable all four Block Public Access settings.",
        priority=RemediationPriority.HIGH,
        effort="low",
        steps=["Step 1", "Step 2"],
    )
    return AnalysisResult(
        request_id="req-test",
        resources_analysed=1,
        findings=[sample_finding],
        recommendations=[rec],
        summary="One high-severity finding detected.",
    )


# ---------------------------------------------------------------------------
# PromptTemplate tests
# ---------------------------------------------------------------------------


class TestPromptTemplate:
    def test_render_basic(self) -> None:
        t = PromptTemplate(
            name="test",
            template="Hello {name}, you have {count} items.",
            required_variables=["name", "count"],
        )
        result = t.render({"name": "Alice", "count": 3})
        assert "Alice" in result
        assert "3" in result

    def test_render_missing_required_raises(self) -> None:
        t = PromptTemplate(
            name="test",
            template="Hello {name}.",
            required_variables=["name"],
        )
        with pytest.raises(ValueError, match="missing required variables"):
            t.render({})

    def test_render_default_variables(self) -> None:
        t = PromptTemplate(
            name="test",
            template="Env: {env}",
            default_variables={"env": "production"},
        )
        result = t.render()
        assert "production" in result

    def test_render_default_overridden(self) -> None:
        t = PromptTemplate(
            name="test",
            template="Env: {env}",
            default_variables={"env": "production"},
        )
        result = t.render({"env": "staging"})
        assert "staging" in result

    def test_conditional_block_included(self) -> None:
        t = PromptTemplate(
            name="test",
            template="Start {% if show %}VISIBLE{% endif %} End",
        )
        result = t.render({"show": True})
        assert "VISIBLE" in result

    def test_conditional_block_excluded(self) -> None:
        t = PromptTemplate(
            name="test",
            template="Start {% if show %}VISIBLE{% endif %} End",
        )
        result = t.render({"show": False})
        assert "VISIBLE" not in result

    def test_unknown_placeholder_preserved(self) -> None:
        t = PromptTemplate(name="test", template="Value: {unknown}")
        result = t.render({})
        assert "{unknown}" in result

    def test_dedent_strips_leading_whitespace(self) -> None:
        t = PromptTemplate(
            name="test",
            template="""
            Hello world
            """,
        )
        assert not t.template.startswith(" ")


class TestTemplateRegistry:
    def test_register_and_get(self) -> None:
        registry = TemplateRegistry()
        t = PromptTemplate(name="my_template", template="Hello {x}")
        registry.register(t)
        assert registry.get("my_template") is t

    def test_get_missing_raises(self) -> None:
        registry = TemplateRegistry()
        with pytest.raises(KeyError):
            registry.get("nonexistent")

    def test_list_templates(self) -> None:
        registry = TemplateRegistry()
        registry.register(PromptTemplate(name="b_template", template="b"))
        registry.register(PromptTemplate(name="a_template", template="a"))
        names = registry.list_templates()
        assert names == sorted(names)

    def test_render_convenience(self) -> None:
        registry = TemplateRegistry()
        registry.register(
            PromptTemplate(name="greet", template="Hi {name}", required_variables=["name"])
        )
        result = registry.render("greet", {"name": "Bob"})
        assert "Bob" in result

    def test_global_registry_has_builtins(self) -> None:
        registry = get_registry()
        names = registry.list_templates()
        assert "system_context" in names
        assert "json_format_instructions" in names


# ---------------------------------------------------------------------------
# InfraAnalysisPromptBuilder tests
# ---------------------------------------------------------------------------


class TestInfraAnalysisPromptBuilder:
    def test_build_for_storage_resource(self, s3_resource: InfraResource) -> None:
        builder = InfraAnalysisPromptBuilder()
        prompt = builder.build_for_resource(s3_resource)
        assert "InfraMind AI" in prompt
        assert "storage" in prompt.lower()
        assert "my-data-bucket" in prompt or "BucketName" in prompt

    def test_build_for_compute_resource(self, ec2_resource: InfraResource) -> None:
        builder = InfraAnalysisPromptBuilder()
        prompt = builder.build_for_resource(ec2_resource)
        assert "compute" in prompt.lower() or "instance" in prompt.lower()

    def test_build_with_focus_areas(self, s3_resource: InfraResource) -> None:
        builder = InfraAnalysisPromptBuilder()
        prompt = builder.build_for_resource(s3_resource, focus_areas=["encryption", "logging"])
        assert "encryption" in prompt.lower()
        assert "logging" in prompt.lower()

    def test_build_for_multiple_resources(
        self, s3_resource: InfraResource, ec2_resource: InfraResource
    ) -> None:
        builder = InfraAnalysisPromptBuilder()
        prompt = builder.build_for_multiple_resources([s3_resource, ec2_resource])
        assert "bucket-001" in prompt
        assert "i-0abc123" in prompt

    def test_build_summary_prompt(self) -> None:
        builder = InfraAnalysisPromptBuilder()
        prompt = builder.build_summary_prompt(findings_json='{"findings": []}')
        assert "Executive Summary" in prompt or "executive" in prompt.lower()

    def test_prompt_includes_json_format_instructions(self, s3_resource: InfraResource) -> None:
        builder = InfraAnalysisPromptBuilder()
        prompt = builder.build_for_resource(s3_resource)
        assert '"findings"' in prompt
        assert '"recommendations"' in prompt


# ---------------------------------------------------------------------------
# SecurityAnalysisLogic tests
# ---------------------------------------------------------------------------


class TestSecurityAnalysisLogic:
    def test_detects_public_s3_bucket(self, s3_resource: InfraResource) -> None:
        logic = SecurityAnalysisLogic()
        result = logic.pre_screen(s3_resource)
        assert result.has_public_access is True
        assert any("Public" in f.title for f in result.pre_findings)

    def test_detects_encryption_disabled_storage(self, s3_resource: InfraResource) -> None:
        logic = SecurityAnalysisLogic()
        result = logic.pre_screen(s3_resource)
        assert result.encryption_disabled is True

    def test_detects_encryption_disabled_database(self, rds_resource: InfraResource) -> None:
        logic = SecurityAnalysisLogic()
        result = logic.pre_screen(rds_resource)
        assert result.encryption_disabled is True

    def test_detects_logging_disabled(self, s3_resource: InfraResource) -> None:
        logic = SecurityAnalysisLogic()
        result = logic.pre_screen(s3_resource)
        assert result.logging_disabled is True

    def test_detects_open_ssh_port(self, ec2_resource: InfraResource) -> None:
        logic = SecurityAnalysisLogic()
        result = logic.pre_screen(ec2_resource)
        assert 22 in result.open_sensitive_ports

    def test_detects_hardcoded_password(self) -> None:
        resource = InfraResource(
            id="r-secret",
            name="app-config",
            resource_type=ResourceType.COMPUTE,
            provider=CloudProvider.AWS,
            configuration={"env": "DATABASE_PASSWORD=supersecret123"},
        )
        logic = SecurityAnalysisLogic()
        result = logic.pre_screen(resource)
        assert any("password" in s["type"] for s in result.suspected_secrets)
        assert any(f.severity == FindingSeverity.CRITICAL for f in result.pre_findings)

    def test_clean_resource_no_pre_findings(self) -> None:
        resource = InfraResource(
            id="r-clean",
            name="clean-bucket",
            resource_type=ResourceType.STORAGE,
            provider=CloudProvider.AWS,
            configuration={
                "PublicAccessBlockConfiguration": {
                    "BlockPublicAcls": True,
                    "IgnorePublicAcls": True,
                    "BlockPublicPolicy": True,
                    "RestrictPublicBuckets": True,
                },
                "ServerSideEncryptionConfiguration": {"Rules": [{"SSE": "aws:kms"}]},
                "LoggingEnabled": {"TargetBucket": "log-bucket"},
            },
        )
        logic = SecurityAnalysisLogic()
        result = logic.pre_screen(resource)
        assert result.has_public_access is False
        assert result.encryption_disabled is False
        assert result.logging_disabled is False


class TestSecurityAnalysisPromptBuilder:
    def test_build_security_analysis(self, s3_resource: InfraResource) -> None:
        builder = SecurityAnalysisPromptBuilder()
        prompt = builder.build_security_analysis(s3_resource)
        assert "security" in prompt.lower()
        assert "bucket-001" in prompt or "my-data-bucket" in prompt

    def test_pre_screen_annotation_included(self, s3_resource: InfraResource) -> None:
        builder = SecurityAnalysisPromptBuilder()
        prompt = builder.build_security_analysis(s3_resource, include_pre_screen_annotation=True)
        assert "Pre-Screen" in prompt

    def test_build_compliance_check(self, rds_resource: InfraResource) -> None:
        builder = SecurityAnalysisPromptBuilder()
        prompt = builder.build_compliance_check(
            rds_resource, frameworks=["CIS", "PCI-DSS"]
        )
        assert "CIS" in prompt
        assert "PCI-DSS" in prompt

    def test_build_threat_model(
        self, s3_resource: InfraResource, ec2_resource: InfraResource
    ) -> None:
        builder = SecurityAnalysisPromptBuilder()
        prompt = builder.build_threat_model([s3_resource, ec2_resource])
        assert "STRIDE" in prompt

    def test_build_cve_analysis(self) -> None:
        builder = SecurityAnalysisPromptBuilder()
        inventory = [{"name": "nginx", "version": "1.18.0"}]
        prompt = builder.build_cve_analysis(inventory)
        assert "CVE" in prompt or "vulnerability" in prompt.lower()

    def test_build_incident_response(self, ec2_resource: InfraResource) -> None:
        builder = SecurityAnalysisPromptBuilder()
        prompt = builder.build_incident_response(
            incident_description="Unauthorised access detected.",
            affected_resources=[ec2_resource],
        )
        assert "Incident" in prompt or "incident" in prompt


# ---------------------------------------------------------------------------
# RiskScoringEngine tests
# ---------------------------------------------------------------------------


class TestRiskScoringEngine:
    def test_score_critical_finding(self, sample_finding: Finding) -> None:
        sample_finding.severity = FindingSeverity.CRITICAL
        sample_finding.risk_score = RiskScore(base_score=9.5, exploitability=1.0, impact=1.0)
        engine = RiskScoringEngine(data_sensitivity=DataSensitivity.CONFIDENTIAL)
        breakdown = engine.score_finding(sample_finding)
        assert breakdown.adjusted_score >= 9.0
        assert breakdown.risk_band == RiskBand.CRITICAL

    def test_environment_modifier_reduces_score(self, sample_finding: Finding) -> None:
        engine_prod = RiskScoringEngine(environment=EnvironmentModifier.PRODUCTION)
        engine_dev = RiskScoringEngine(environment=EnvironmentModifier.DEVELOPMENT)
        bd_prod = engine_prod.score_finding(sample_finding)
        bd_dev = engine_dev.score_finding(sample_finding)
        assert bd_dev.adjusted_score < bd_prod.adjusted_score

    def test_internet_exposed_increases_score(self, sample_finding: Finding) -> None:
        engine_internal = RiskScoringEngine(internet_exposed=False)
        engine_exposed = RiskScoringEngine(internet_exposed=True)
        bd_internal = engine_internal.score_finding(sample_finding)
        bd_exposed = engine_exposed.score_finding(sample_finding)
        assert bd_exposed.adjusted_score >= bd_internal.adjusted_score

    def test_score_capped_at_10(self) -> None:
        finding = Finding(
            id="F-MAX",
            resource_id="r-1",
            title="Max Risk",
            description="",
            severity=FindingSeverity.CRITICAL,
            risk_score=RiskScore(base_score=10.0, exploitability=1.0, impact=1.0),
        )
        engine = RiskScoringEngine(
            data_sensitivity=DataSensitivity.PCI,
            internet_exposed=True,
        )
        breakdown = engine.score_finding(finding)
        assert breakdown.adjusted_score <= 10.0

    def test_aggregate_empty(self) -> None:
        engine = RiskScoringEngine()
        result = engine.aggregate([])
        assert result.overall_score == 0.0
        assert result.risk_band == RiskBand.NEGLIGIBLE
        assert result.finding_count == 0

    def test_aggregate_counts(self, sample_finding: Finding) -> None:
        critical = Finding(
            id="F-C",
            resource_id="r-1",
            title="Critical",
            description="",
            severity=FindingSeverity.CRITICAL,
            risk_score=RiskScore(base_score=9.5),
        )
        engine = RiskScoringEngine()
        result = engine.aggregate([sample_finding, critical])
        assert result.critical_count == 1
        assert result.high_count == 1
        assert result.has_critical

    def test_from_context(self) -> None:
        engine = RiskScoringEngine.from_context(
            {"environment": "staging", "data_sensitivity": "pii", "internet_exposed": True}
        )
        assert engine.environment == EnvironmentModifier.STAGING
        assert engine.data_sensitivity == DataSensitivity.PII
        assert engine.internet_exposed is True

    def test_from_context_invalid_values_use_defaults(self) -> None:
        engine = RiskScoringEngine.from_context(
            {"environment": "invalid", "data_sensitivity": "invalid"}
        )
        assert engine.environment == EnvironmentModifier.PRODUCTION
        assert engine.data_sensitivity == DataSensitivity.INTERNAL


class TestScoreHelpers:
    @pytest.mark.parametrize(
        "score,expected_band",
        [
            (9.5, RiskBand.CRITICAL),
            (9.0, RiskBand.CRITICAL),
            (8.9, RiskBand.HIGH),
            (7.0, RiskBand.HIGH),
            (6.9, RiskBand.MEDIUM),
            (4.0, RiskBand.MEDIUM),
            (3.9, RiskBand.LOW),
            (0.1, RiskBand.LOW),
            (0.0, RiskBand.NEGLIGIBLE),
        ],
    )
    def test_score_to_risk_band(self, score: float, expected_band: RiskBand) -> None:
        assert score_to_risk_band(score) == expected_band

    @pytest.mark.parametrize(
        "score,expected_severity",
        [
            (9.0, FindingSeverity.CRITICAL),
            (7.0, FindingSeverity.HIGH),
            (4.0, FindingSeverity.MEDIUM),
            (0.1, FindingSeverity.LOW),
            (0.0, FindingSeverity.INFO),
        ],
    )
    def test_severity_from_score(self, score: float, expected_severity: FindingSeverity) -> None:
        assert severity_from_score(score) == expected_severity


# ---------------------------------------------------------------------------
# ResponseParser tests
# ---------------------------------------------------------------------------


class TestResponseParser:
    def test_parse_valid_json(self) -> None:
        raw = json.dumps({
            "summary": "Two findings found.",
            "findings": [
                {
                    "id": "F-1",
                    "resource_id": "r-1",
                    "title": "Open port",
                    "description": "Port 22 is open.",
                    "severity": "high",
                    "risk_score": {"base_score": 7.5, "exploitability": 0.8, "impact": 0.9},
                }
            ],
            "recommendations": [
                {
                    "id": "R-1",
                    "finding_ids": ["F-1"],
                    "title": "Close port 22",
                    "description": "Restrict port 22.",
                    "priority": "high",
                    "effort": "low",
                    "steps": ["Remove rule."],
                }
            ],
        })
        parser = ResponseParser()
        result = parser.parse("req-1", "r-1", raw)
        assert len(result.findings) == 1
        assert result.findings[0].severity == FindingSeverity.HIGH
        assert len(result.recommendations) == 1
        assert result.summary == "Two findings found."

    def test_parse_json_in_markdown_fence(self) -> None:
        payload = {"summary": "ok", "findings": [], "recommendations": []}
        raw = f"Here is the result:\n```json\n{json.dumps(payload)}\n```\nDone."
        parser = ResponseParser()
        result = parser.parse("req-2", "r-2", raw)
        assert result.summary == "ok"

    def test_parse_invalid_json_returns_error_result(self) -> None:
        parser = ResponseParser()
        result = parser.parse("req-3", "r-3", "not json at all")
        assert "parse" in result.summary.lower() or "failed" in result.summary.lower()

    def test_parse_unknown_severity_defaults_to_medium(self) -> None:
        raw = json.dumps({
            "summary": "",
            "findings": [
                {
                    "id": "F-1",
                    "resource_id": "r-1",
                    "title": "T",
                    "description": "D",
                    "severity": "banana",
                    "risk_score": {"base_score": 5.0},
                }
            ],
            "recommendations": [],
        })
        parser = ResponseParser()
        result = parser.parse("req-4", "r-1", raw)
        assert result.findings[0].severity == FindingSeverity.MEDIUM

    def test_parse_multiple_merges_findings(self) -> None:
        def make_response(resource_id: str, title: str) -> dict:
            return {
                "resource_id": resource_id,
                "raw_text": json.dumps({
                    "summary": f"summary for {resource_id}",
                    "findings": [{
                        "id": f"F-{resource_id}",
                        "resource_id": resource_id,
                        "title": title,
                        "description": "desc",
                        "severity": "medium",
                        "risk_score": {"base_score": 5.0},
                    }],
                    "recommendations": [],
                }),
            }

        parser = ResponseParser()
        result = parser.parse_multiple(
            "req-m",
            [make_response("r-1", "Finding A"), make_response("r-2", "Finding B")],
        )
        assert result.resources_analysed == 2
        assert len(result.findings) == 2


class TestExtractJson:
    def test_plain_json(self) -> None:
        raw = '{"key": "value"}'
        assert _extract_json(raw) == '{"key": "value"}'

    def test_fenced_json(self) -> None:
        raw = '```json\n{"key": "value"}\n```'
        assert _extract_json(raw).strip() == '{"key": "value"}'

    def test_json_embedded_in_text(self) -> None:
        raw = 'Here is the answer: {"key": "value"} end.'
        extracted = _extract_json(raw)
        assert "key" in extracted


# ---------------------------------------------------------------------------
# ResponseFormatter tests
# ---------------------------------------------------------------------------


class TestResponseFormatter:
    def test_to_text_contains_request_id(self, sample_result: AnalysisResult) -> None:
        formatter = ResponseFormatter()
        text = formatter.to_text(sample_result)
        assert "req-test" in text

    def test_to_text_contains_finding_title(self, sample_result: AnalysisResult) -> None:
        formatter = ResponseFormatter()
        text = formatter.to_text(sample_result)
        assert "S3 Bucket Publicly Accessible" in text

    def test_to_text_verbose_includes_description(self, sample_result: AnalysisResult) -> None:
        formatter = ResponseFormatter()
        text = formatter.to_text(sample_result, verbose=True)
        assert "The bucket allows public access." in text

    def test_to_markdown_contains_heading(self, sample_result: AnalysisResult) -> None:
        formatter = ResponseFormatter()
        md = formatter.to_markdown(sample_result)
        assert "# InfraMind AI" in md

    def test_to_markdown_contains_finding_table(self, sample_result: AnalysisResult) -> None:
        formatter = ResponseFormatter()
        md = formatter.to_markdown(sample_result)
        assert "S3 Bucket Publicly Accessible" in md

    def test_to_json_is_valid_json(self, sample_result: AnalysisResult) -> None:
        formatter = ResponseFormatter()
        json_str = formatter.to_json(sample_result)
        parsed = json.loads(json_str)
        assert parsed["request_id"] == "req-test"
        assert len(parsed["findings"]) == 1


# ---------------------------------------------------------------------------
# RecommendationEngine tests
# ---------------------------------------------------------------------------


class TestRecommendationEngine:
    def test_generate_from_s3_public_access_finding(self) -> None:
        finding = Finding(
            id="F-S3-PUB",
            resource_id="bucket-001",
            title="S3 Bucket Publicly Accessible",
            description="Public access is not blocked.",
            severity=FindingSeverity.HIGH,
            risk_score=RiskScore(base_score=8.0, exploitability=0.9, impact=0.9),
        )
        engine = RecommendationEngine()
        recs = engine.generate([finding])
        assert len(recs) > 0
        # Should match PB-S3-PUBLIC-ACCESS playbook
        titles = [r.title for r in recs]
        assert any("Public Access" in t or "public" in t.lower() for t in titles)

    def test_generate_ssh_finding_matches_playbook(self) -> None:
        finding = Finding(
            id="F-SSH",
            resource_id="i-abc",
            title="Open SSH Port 22",
            description="Port 22 is open to 0.0.0.0/0.",
            severity=FindingSeverity.HIGH,
            risk_score=RiskScore(base_score=7.5),
        )
        engine = RecommendationEngine()
        recs = engine.generate([finding])
        assert any("SSH" in r.title or "22" in r.title or "ssh" in r.title.lower() for r in recs)

    def test_generate_creates_fallback_recommendation(self) -> None:
        finding = Finding(
            id="F-UNKNOWN",
            resource_id="r-xyz",
            title="Some Very Obscure Finding Without Playbook",
            description="Something unusual.",
            severity=FindingSeverity.MEDIUM,
            risk_score=RiskScore(base_score=5.0),
        )
        engine = RecommendationEngine()
        recs = engine.generate([finding])
        assert len(recs) == 1
        assert "F-UNKNOWN" in recs[0].finding_ids

    def test_generate_deduplicates_recommendations(self) -> None:
        findings = [
            Finding(
                id=f"F-S3-{i}",
                resource_id=f"bucket-{i}",
                title="S3 Bucket Publicly Accessible",
                description="Public access.",
                severity=FindingSeverity.HIGH,
                risk_score=RiskScore(base_score=8.0),
            )
            for i in range(3)
        ]
        engine = RecommendationEngine()
        recs = engine.generate(findings)
        titles = [r.title for r in recs]
        # All three findings map to the same playbook → should be deduplicated
        assert len(titles) == len(set(titles))

    def test_generate_enriches_existing_recommendations(self) -> None:
        finding = Finding(
            id="F-1",
            resource_id="r-1",
            title="Hard-coded secret in config",
            description="API key found.",
            severity=FindingSeverity.CRITICAL,
            risk_score=RiskScore(base_score=9.0),
        )
        existing_rec = Recommendation(
            id="R-AI",
            finding_ids=["F-1"],
            title="Remove Hard-Coded Secrets from Configuration",
            description="AI generated guidance.",
            priority=RemediationPriority.IMMEDIATE,
            effort="medium",
        )
        engine = RecommendationEngine()
        recs = engine.generate([finding], existing_recommendations=[existing_rec])
        # Enriched recommendation should have steps from playbook
        enriched = next(r for r in recs if r.id == "R-AI")
        assert len(enriched.steps) > 0

    def test_priority_immediate_for_critical_finding(self) -> None:
        finding = Finding(
            id="F-CRIT",
            resource_id="r-1",
            title="Critical Unpatched Vulnerability",
            description="No playbook match but very high score.",
            severity=FindingSeverity.CRITICAL,
            risk_score=RiskScore(base_score=9.5),
        )
        engine = RecommendationEngine()
        recs = engine.generate([finding])
        assert recs[0].priority == RemediationPriority.IMMEDIATE

    def test_sorted_by_priority(self) -> None:
        findings = [
            Finding(
                id="F-LOW",
                resource_id="r",
                title="Low risk info",
                description="",
                severity=FindingSeverity.LOW,
                risk_score=RiskScore(base_score=1.0),
            ),
            Finding(
                id="F-CRIT",
                resource_id="r",
                title="Critical outage risk",
                description="",
                severity=FindingSeverity.CRITICAL,
                risk_score=RiskScore(base_score=9.5),
            ),
        ]
        engine = RecommendationEngine()
        recs = engine.generate(findings)
        priorities = [list(RemediationPriority).index(r.priority) for r in recs]
        assert priorities == sorted(priorities)


# ---------------------------------------------------------------------------
# AIOrchestrator end-to-end tests
# ---------------------------------------------------------------------------


class _DuplicateResponseProvider:
    """Mock LLM provider that returns a finding duplicating a pre-screen result."""

    def __init__(self, resource_id: str) -> None:
        self._resource_id = resource_id

    def complete(self, prompt: str, **kwargs: Any) -> str:  # noqa: ARG002
        return json.dumps({
            "summary": "test",
            "findings": [{
                "id": "F-DUP",
                "resource_id": self._resource_id,
                "title": "Storage Resource Publicly Accessible",  # same as pre-screen
                "description": "Duplicate.",
                "severity": "high",
                "risk_score": {"base_score": 8.0},
            }],
            "recommendations": [],
        })


class TestAIOrchestrator:
    def test_analyse_returns_analysis_result(self, s3_resource: InfraResource) -> None:
        request = AnalysisRequest(
            request_id="req-e2e-1",
            resources=[s3_resource],
        )
        orchestrator = AIOrchestrator(provider=MockProvider())
        result = orchestrator.analyse(request)
        assert isinstance(result, AnalysisResult)
        assert result.request_id == "req-e2e-1"
        assert result.resources_analysed == 1

    def test_analyse_includes_pre_screen_findings(self, s3_resource: InfraResource) -> None:
        request = AnalysisRequest(request_id="req-e2e-2", resources=[s3_resource])
        config = OrchestratorConfig(include_pre_screen=True)
        orchestrator = AIOrchestrator(provider=MockProvider(), config=config)
        result = orchestrator.analyse(request)
        # s3_resource has public access, encryption, and logging issues
        assert len(result.findings) > 0

    def test_analyse_multiple_resources(
        self, s3_resource: InfraResource, ec2_resource: InfraResource
    ) -> None:
        request = AnalysisRequest(
            request_id="req-e2e-3",
            resources=[s3_resource, ec2_resource],
        )
        orchestrator = AIOrchestrator(provider=MockProvider())
        result = orchestrator.analyse(request)
        assert result.resources_analysed == 2

    def test_analyse_security_mode(self, ec2_resource: InfraResource) -> None:
        request = AnalysisRequest(request_id="req-e2e-4", resources=[ec2_resource])
        config = OrchestratorConfig(mode="security")
        orchestrator = AIOrchestrator(provider=MockProvider(), config=config)
        result = orchestrator.analyse(request)
        assert isinstance(result, AnalysisResult)

    def test_analyse_holistic_mode(
        self, s3_resource: InfraResource, rds_resource: InfraResource
    ) -> None:
        request = AnalysisRequest(
            request_id="req-e2e-5",
            resources=[s3_resource, rds_resource],
        )
        config = OrchestratorConfig(analyse_per_resource=False)
        orchestrator = AIOrchestrator(provider=MockProvider(), config=config)
        result = orchestrator.analyse(request)
        assert result.resources_analysed == 2

    def test_format_result_text(self, s3_resource: InfraResource) -> None:
        request = AnalysisRequest(request_id="req-fmt-1", resources=[s3_resource])
        orchestrator = AIOrchestrator(provider=MockProvider())
        result = orchestrator.analyse(request)
        text = orchestrator.format_result(result, fmt="text")
        assert "InfraMind AI" in text

    def test_format_result_markdown(self, s3_resource: InfraResource) -> None:
        request = AnalysisRequest(request_id="req-fmt-2", resources=[s3_resource])
        orchestrator = AIOrchestrator(provider=MockProvider())
        result = orchestrator.analyse(request)
        md = orchestrator.format_result(result, fmt="markdown")
        assert "# InfraMind AI" in md

    def test_format_result_json(self, s3_resource: InfraResource) -> None:
        request = AnalysisRequest(request_id="req-fmt-3", resources=[s3_resource])
        orchestrator = AIOrchestrator(provider=MockProvider())
        result = orchestrator.analyse(request)
        json_str = orchestrator.format_result(result, fmt="json")
        parsed = json.loads(json_str)
        assert parsed["request_id"] == "req-fmt-3"

    def test_overall_risk_score_set(self, s3_resource: InfraResource) -> None:
        request = AnalysisRequest(request_id="req-score", resources=[s3_resource])
        config = OrchestratorConfig(include_pre_screen=True)
        orchestrator = AIOrchestrator(provider=MockProvider(), config=config)
        result = orchestrator.analyse(request)
        if result.findings:
            assert result.overall_risk_score is not None
            assert 0.0 <= result.overall_risk_score <= 10.0

    def test_no_pre_screen_produces_no_extra_findings(
        self, s3_resource: InfraResource
    ) -> None:
        request = AnalysisRequest(request_id="req-noscreen", resources=[s3_resource])
        config = OrchestratorConfig(include_pre_screen=False)
        orchestrator = AIOrchestrator(provider=MockProvider(), config=config)
        result = orchestrator.analyse(request)
        # MockProvider returns no findings, no pre-screen → 0 findings
        assert len(result.findings) == 0

    def test_metadata_contains_risk_band(self, s3_resource: InfraResource) -> None:
        request = AnalysisRequest(request_id="req-meta", resources=[s3_resource])
        config = OrchestratorConfig(include_pre_screen=True)
        orchestrator = AIOrchestrator(provider=MockProvider(), config=config)
        result = orchestrator.analyse(request)
        assert "risk_band" in result.metadata

    def test_deduplication_prevents_duplicate_findings(
        self, s3_resource: InfraResource
    ) -> None:
        """Mock provider returns a finding that duplicates a pre-screen finding."""
        request = AnalysisRequest(request_id="req-dup", resources=[s3_resource])
        config = OrchestratorConfig(include_pre_screen=True)
        orchestrator = AIOrchestrator(
            provider=_DuplicateResponseProvider(s3_resource.id), config=config
        )
        result = orchestrator.analyse(request)

        titles = [f.title for f in result.findings]
        assert len(titles) == len(set(titles)), "Duplicate findings were not removed"
