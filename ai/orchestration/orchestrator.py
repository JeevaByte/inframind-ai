"""
AI orchestration logic for InfraMind AI.

The ``AIOrchestrator`` is the top-level entry point.  It:

1. Accepts an ``AnalysisRequest``
2. Runs rule-based pre-screening on each resource (SecurityAnalysisLogic)
3. Builds per-resource prompts (InfraAnalysisPromptBuilder or
   SecurityAnalysisPromptBuilder depending on mode)
4. Sends prompts to the configured LLM backend
5. Parses and merges responses (ResponseParser)
6. Adjusts risk scores (RiskScoringEngine)
7. Generates/enriches recommendations (RecommendationEngine)
8. Returns a fully populated ``AnalysisResult``

The module is designed to be LLM-provider-agnostic.  A pluggable
``LLMProvider`` protocol is defined so that OpenAI, Anthropic, Azure
OpenAI, or a local model can be wired in at runtime.
"""

from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from ai.formatting.response_formatter import ResponseFormatter, ResponseParser
from ai.models.schemas import (
    AnalysisRequest,
    AnalysisResult,
    CloudProvider,
    Finding,
)
from ai.prompts.infra_analysis import InfraAnalysisPromptBuilder
from ai.prompts.security_analysis import SecurityAnalysisLogic, SecurityAnalysisPromptBuilder
from ai.recommendation.engine import RecommendationEngine
from ai.risk.scoring import DataSensitivity, EnvironmentModifier, RiskScoringEngine

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LLM Provider protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class LLMProvider(Protocol):
    """
    Protocol that any LLM backend must satisfy.

    Implementors should be callable and return the model's text response.
    """

    def complete(self, prompt: str, **kwargs: Any) -> str:
        """
        Send *prompt* to the model and return its text response.

        Parameters
        ----------
        prompt:
            The full prompt string (system + user turns combined).
        **kwargs:
            Provider-specific parameters (temperature, max_tokens, etc.).

        Returns
        -------
        str
            Raw text response from the model.
        """
        ...


# ---------------------------------------------------------------------------
# Built-in LLM provider implementations
# ---------------------------------------------------------------------------


class OpenAIProvider:
    """
    OpenAI ChatCompletion provider.

    Requires the ``openai`` package: pip install openai

    Usage::

        provider = OpenAIProvider(api_key="sk-...", model="gpt-4o")
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> None:
        try:
            import openai  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "openai package is required for OpenAIProvider. "
                "Install it with: pip install openai"
            ) from exc
        self._client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def complete(self, prompt: str, **kwargs: Any) -> str:
        response = self._client.chat.completions.create(
            model=kwargs.get("model", self.model),
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
        )
        return response.choices[0].message.content or ""


class AnthropicProvider:
    """
    Anthropic Claude provider.

    Requires the ``anthropic`` package: pip install anthropic

    Usage::

        provider = AnthropicProvider(api_key="...", model="claude-3-5-sonnet-20241022")
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
    ) -> None:
        try:
            import anthropic  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "anthropic package is required for AnthropicProvider. "
                "Install it with: pip install anthropic"
            ) from exc
        self._client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens

    def complete(self, prompt: str, **kwargs: Any) -> str:
        message = self._client.messages.create(
            model=kwargs.get("model", self.model),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text if message.content else ""


class MockProvider:
    """
    Deterministic mock provider for testing without a real LLM.

    Returns a minimal valid JSON response with zero findings.
    """

    def complete(self, prompt: str, **kwargs: Any) -> str:  # noqa: ARG002  # prompt intentionally ignored by mock
        return (
            '{"summary": "Mock analysis complete. No findings detected.", '
            '"findings": [], "recommendations": []}'
        )


# ---------------------------------------------------------------------------
# Orchestrator configuration
# ---------------------------------------------------------------------------


@dataclass
class OrchestratorConfig:
    """
    Configuration for the ``AIOrchestrator``.

    Parameters
    ----------
    mode:
        ``"infra"`` for infrastructure + operational analysis,
        ``"security"`` for security-focused analysis.
        Defaults to ``"infra"``.
    analyse_per_resource:
        If ``True``, send a separate LLM request per resource.
        If ``False``, send one holistic request for all resources.
        Defaults to ``True``.
    include_pre_screen:
        Include rule-based pre-screening findings.  Defaults to ``True``.
    environment:
        Business context for risk adjustment.
    data_sensitivity:
        Data sensitivity level for risk adjustment.
    internet_exposed:
        Whether the resources are internet-facing.
    llm_kwargs:
        Extra keyword arguments forwarded to ``LLMProvider.complete()``.
    """

    mode: str = "infra"
    analyse_per_resource: bool = True
    include_pre_screen: bool = True
    environment: EnvironmentModifier = EnvironmentModifier.PRODUCTION
    data_sensitivity: DataSensitivity = DataSensitivity.INTERNAL
    internet_exposed: bool = False
    llm_kwargs: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------


class AIOrchestrator:
    """
    Top-level AI analysis orchestrator.

    Usage::

        from ai.orchestration.orchestrator import AIOrchestrator, OpenAIProvider

        provider = OpenAIProvider(api_key="sk-...")
        orchestrator = AIOrchestrator(provider=provider)
        result = orchestrator.analyse(request)
        print(result.overall_risk_score)
    """

    def __init__(
        self,
        provider: LLMProvider,
        config: Optional[OrchestratorConfig] = None,
    ) -> None:
        self._provider = provider
        self._config = config or OrchestratorConfig()
        self._infra_builder = InfraAnalysisPromptBuilder()
        self._security_builder = SecurityAnalysisPromptBuilder()
        self._security_logic = SecurityAnalysisLogic()
        self._parser = ResponseParser()
        self._formatter = ResponseFormatter()
        self._rec_engine = RecommendationEngine()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyse(self, request: AnalysisRequest) -> AnalysisResult:
        """
        Run a full analysis for the given request.

        Parameters
        ----------
        request:
            The analysis request containing resources and optional context.

        Returns
        -------
        AnalysisResult
            Fully populated analysis result with findings, recommendations,
            risk scores, and executive summary.
        """
        logger.info(
            "Starting analysis request=%s resources=%d mode=%s",
            request.request_id,
            len(request.resources),
            self._config.mode,
        )

        # 1. Rule-based pre-screening
        pre_screen_findings: List[Finding] = []
        if self._config.include_pre_screen:
            for resource in request.resources:
                pre_result = self._security_logic.pre_screen(resource)
                pre_screen_findings.extend(pre_result.pre_findings)

        # 2. Build prompts and call LLM
        if self._config.analyse_per_resource:
            raw_result = self._analyse_per_resource(request)
        else:
            raw_result = self._analyse_holistic(request)

        # 3. Merge pre-screening findings
        all_findings = pre_screen_findings + raw_result.findings

        # 4. Deduplicate findings by title + resource_id
        all_findings = _deduplicate_findings(all_findings)

        # 5. Adjust risk scores
        scorer = RiskScoringEngine(
            environment=self._config.environment,
            data_sensitivity=self._config.data_sensitivity,
            internet_exposed=self._config.internet_exposed,
        )
        aggregate = scorer.aggregate(all_findings)

        # Apply adjusted scores back to findings
        score_map = {b.finding_id: b.adjusted_score for b in aggregate.breakdowns}
        for finding in all_findings:
            if finding.id in score_map:
                finding.risk_score.overall_score = score_map[finding.id]

        # 6. Generate / enrich recommendations
        recommendations = self._rec_engine.generate(
            findings=all_findings,
            existing_recommendations=raw_result.recommendations or None,
        )

        # 7. Build final result
        result = AnalysisResult(
            request_id=request.request_id,
            resources_analysed=len(request.resources),
            findings=all_findings,
            recommendations=recommendations,
            summary=raw_result.summary,
            overall_risk_score=aggregate.overall_score,
            metadata={
                "risk_band": aggregate.risk_band.value,
                "critical_count": aggregate.critical_count,
                "high_count": aggregate.high_count,
                "medium_count": aggregate.medium_count,
                "low_count": aggregate.low_count,
                "weighted_average_score": aggregate.weighted_average,
                "mode": self._config.mode,
                "pre_screen_finding_count": len(pre_screen_findings),
            },
        )

        logger.info(
            "Analysis complete request=%s findings=%d recommendations=%d score=%.1f",
            request.request_id,
            len(result.findings),
            len(result.recommendations),
            result.overall_risk_score or 0.0,
        )

        return result

    def format_result(self, result: AnalysisResult, fmt: str = "text") -> str:
        """
        Format an ``AnalysisResult`` for output.

        Parameters
        ----------
        result:
            The analysis result to format.
        fmt:
            Output format: ``"text"``, ``"markdown"``, or ``"json"``.
        """
        fmt = fmt.lower()
        if fmt == "markdown":
            return self._formatter.to_markdown(result)
        if fmt == "json":
            return self._formatter.to_json(result)
        return self._formatter.to_text(result, verbose=True)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _analyse_per_resource(self, request: AnalysisRequest) -> AnalysisResult:
        """Send one LLM request per resource and merge results."""
        responses = []
        for resource in request.resources:
            prompt = self._build_prompt(
                resources=[resource],
                focus_areas=request.focus_areas,
                provider=request.provider_hint or CloudProvider.AWS,
                context=str(request.context),
            )
            logger.debug("Calling LLM for resource=%s", resource.id)
            raw_text = self._provider.complete(prompt, **self._config.llm_kwargs)
            responses.append({"resource_id": resource.id, "raw_text": raw_text})

        return self._parser.parse_multiple(
            request_id=request.request_id,
            responses=responses,
        )

    def _analyse_holistic(self, request: AnalysisRequest) -> AnalysisResult:
        """Send a single holistic LLM request for all resources."""
        prompt = self._build_prompt(
            resources=request.resources,
            focus_areas=request.focus_areas,
            provider=request.provider_hint or CloudProvider.AWS,
            context=str(request.context),
        )
        logger.debug("Calling LLM holistic for %d resources", len(request.resources))
        raw_text = self._provider.complete(prompt, **self._config.llm_kwargs)
        return self._parser.parse(
            request_id=request.request_id,
            resource_id="multi-resource",
            raw_text=raw_text,
            resources_analysed=len(request.resources),
        )

    def _build_prompt(
        self,
        resources: List,
        focus_areas: List[str],
        provider: CloudProvider,
        context: str,
    ) -> str:
        if self._config.mode == "security":
            if len(resources) == 1:
                return self._security_builder.build_security_analysis(
                    resource=resources[0],
                    focus_areas=focus_areas or None,
                    extra_context=context,
                )
            return self._security_builder.build_threat_model(
                resources=resources,
                extra_context=context,
            )
        else:
            if len(resources) == 1:
                return self._infra_builder.build_for_resource(
                    resource=resources[0],
                    focus_areas=focus_areas or None,
                    extra_context=context,
                )
            return self._infra_builder.build_for_multiple_resources(
                resources=resources,
                focus_areas=focus_areas or None,
                extra_context=context,
                provider=provider,
            )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _deduplicate_findings(findings: List[Finding]) -> List[Finding]:
    """Remove duplicate findings based on title + resource_id."""
    seen: set[str] = set()
    deduped: List[Finding] = []
    for f in findings:
        key = f"{f.resource_id}::{f.title.lower().strip()}"
        if key not in seen:
            seen.add(key)
            deduped.append(f)
    return deduped
