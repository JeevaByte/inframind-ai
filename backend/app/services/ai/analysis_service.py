from __future__ import annotations

import uuid
from typing import Any, Dict, List

from app.config import Settings
from app.models.common import AnalysisType, Finding, FindingCategory, InfraFileType, Severity
from app.services.ai.infra_parser import InfrastructureParser, ParsedInfrastructureContext
from app.services.ai.openai_client import OpenAIAnalysisClient
from app.services.ai.prompt_builder import AIPromptBuilder
from app.services.ai.response_parser import AIAnalysisPayload, AIResponseParser
from app.services.ai.scoring import score_findings


_CATEGORY_TO_PREFIX = {
    FindingCategory.SECURITY: "SEC",
    FindingCategory.RELIABILITY: "REL",
    FindingCategory.COST: "COST",
    FindingCategory.COMPLIANCE: "COMP",
}


class AIAnalysisService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._parser = InfrastructureParser()
        self._prompt_builder = AIPromptBuilder()
        self._response_parser = AIResponseParser()
        self._client = None if settings.use_mock_ai or not settings.openai_api_key else OpenAIAnalysisClient(settings)

    async def analyze(
        self,
        *,
        content: str,
        filename: str,
        file_type: InfraFileType,
        analysis_type: AnalysisType,
        options: Dict[str, Any],
    ) -> Dict[str, Any]:
        context = self._parser.parse(
            file_name=filename,
            content=content,
            file_type=file_type,
            max_excerpt_chars=self._settings.openai_max_excerpt_chars,
        )

        payload: AIAnalysisPayload
        mode = "heuristic"

        if self._client is not None:
            prompts = self._prompt_builder.build(context=context, analysis_type=analysis_type)
            try:
                response = await self._client.analyze(system_prompt=prompts["system"], user_prompt=prompts["user"])
                payload = self._response_parser.parse(response["raw_content"])
                mode = "openai"
            except Exception:
                payload = self._build_fallback_payload(context=context, analysis_type=analysis_type)
                mode = "fallback"
        else:
            payload = self._build_fallback_payload(context=context, analysis_type=analysis_type)

        findings = self._build_findings(payload, context)
        scores = score_findings((finding.category, finding.severity) for finding in findings)

        return {
            "findings": findings,
            "summary": payload.summary,
            "score": payload.score or scores.overall_score,
            "security_score": payload.security_score if payload.security_score is not None else scores.security_score,
            "reliability_score": payload.reliability_score if payload.reliability_score is not None else scores.reliability_score,
            "cost_optimization_score": payload.cost_optimization_score if payload.cost_optimization_score is not None else scores.cost_optimization_score,
            "compliance_score": payload.compliance_score if payload.compliance_score is not None else scores.compliance_score,
            "deployment_readiness": payload.deployment_readiness or scores.deployment_readiness,
            "architecture_summary": payload.architecture_summary or self._build_architecture_summary(context),
            "top_recommendations": payload.top_recommendations,
            "metadata": {
                "analysis_mode": mode,
                "file_type": file_type.value,
                "provider_hints": context.providers,
                "resource_count": len(context.resources),
                "parser_summary": context.summary,
                "options": options,
            },
        }

    def _build_fallback_payload(self, *, context: ParsedInfrastructureContext, analysis_type: AnalysisType) -> AIAnalysisPayload:
        allowed_categories = self._categories_for_analysis_type(analysis_type)
        selected_signals = [signal for signal in context.signals if signal.category in allowed_categories][:8]

        if not selected_signals:
            selected_signals = [
                context.signals[0]
                for _ in []
            ]

        findings = [
            {
                "title": signal.title,
                "severity": signal.severity,
                "category": signal.category,
                "description": signal.description,
                "recommendation": signal.recommendation,
                "estimated_impact": signal.estimated_impact,
            }
            for signal in selected_signals
        ]

        if findings:
            summary = f"AI-assisted analysis identified {len(findings)} notable issue(s) across {len(context.resources) or 1} infrastructure component(s)."
        else:
            summary = "AI-assisted analysis did not detect major issues in the uploaded infrastructure file."

        fallback = {
            "summary": summary,
            "score": 88 if not findings else max(20, 100 - 12 * len(findings)),
            "deployment_readiness": "Ready with minor follow-up" if not findings else "Needs remediation",
            "findings": findings,
            "architecture_summary": self._build_architecture_summary(context),
            "top_recommendations": [signal.recommendation for signal in selected_signals[:3]],
        }
        return self._response_parser.parse(fallback)

    def _build_findings(self, payload: AIAnalysisPayload, context: ParsedInfrastructureContext) -> List[Finding]:
        findings: List[Finding] = []
        for index, item in enumerate(payload.findings, start=1):
            category = FindingCategory(item.category)
            severity = Severity(item.severity)
            findings.append(
                Finding(
                    id=str(uuid.uuid4()),
                    rule_id=f"{_CATEGORY_TO_PREFIX[category]}-{index:03d}",
                    category=category,
                    title=item.title,
                    description=item.description,
                    severity=severity,
                    recommendation=item.recommendation,
                    resource=context.resources[0].get("name") if context.resources else None,
                    references=[],
                    metadata={
                        "estimated_impact": item.estimated_impact,
                        "estimated_cost": item.estimated_impact if category == FindingCategory.COST else "N/A",
                    },
                )
            )
        return findings

    def _build_architecture_summary(self, context: ParsedInfrastructureContext) -> str:
        resource_types = sorted({resource.get("type", "unknown") for resource in context.resources})
        providers = ", ".join(context.providers) if context.providers else "unknown provider"
        if not resource_types:
            return f"The uploaded {context.file_type.value} file was parsed for {providers}, but it did not expose structured resources beyond the raw configuration content."
        return (
            f"The uploaded {context.file_type.value} file defines {len(context.resources)} component(s) "
            f"across {providers}. Key infrastructure elements include {', '.join(resource_types[:6])}."
        )

    def _categories_for_analysis_type(self, analysis_type: AnalysisType) -> set[str]:
        if analysis_type == AnalysisType.SECURITY:
            return {"security"}
        if analysis_type == AnalysisType.RELIABILITY:
            return {"reliability"}
        if analysis_type == AnalysisType.COST:
            return {"cost"}
        if analysis_type == AnalysisType.COMPLIANCE:
            return {"compliance"}
        return {"security", "reliability", "cost", "compliance"}