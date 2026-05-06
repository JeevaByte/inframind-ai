"""
AI response formatting for InfraMind AI.

This module is responsible for:
- Parsing raw LLM responses (JSON or plain text) into structured objects
- Validating parsed data against Pydantic schemas
- Normalising and sanitising AI output before it reaches consumers
- Providing a human-readable text formatter for CLI / reporting output
- Generating markdown reports from ``AnalysisResult`` objects
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from ai.models.schemas import (
    AnalysisResult,
    Finding,
    FindingSeverity,
    Recommendation,
    RemediationPriority,
    RiskScore,
)


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


def _extract_json(text: str) -> str:
    """
    Extract a JSON payload from *text*.

    Handles:
    - Plain JSON strings
    - JSON embedded in markdown code fences (```json ... ```)
    - Leading/trailing whitespace and commentary
    """
    # Try to strip markdown fences first
    fenced = _JSON_FENCE_RE.search(text)
    if fenced:
        return fenced.group(1).strip()

    # Attempt to find the outermost JSON object
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
        return text[brace_start : brace_end + 1]

    return text.strip()


def _parse_finding(raw: Dict[str, Any], resource_id: str) -> Finding:
    """Parse a raw dict into a ``Finding``, applying sensible defaults."""
    risk_raw = raw.get("risk_score", {})
    risk = RiskScore(
        base_score=float(risk_raw.get("base_score", 5.0)),
        exploitability=float(risk_raw.get("exploitability", 0.5)),
        impact=float(risk_raw.get("impact", 0.5)),
        rationale=risk_raw.get("rationale", ""),
    )

    severity_str = str(raw.get("severity", "medium")).lower()
    try:
        severity = FindingSeverity(severity_str)
    except ValueError:
        severity = FindingSeverity.MEDIUM

    return Finding(
        id=str(raw.get("id", uuid.uuid4())),
        resource_id=str(raw.get("resource_id", resource_id)),
        title=str(raw.get("title", "Unnamed Finding")),
        description=str(raw.get("description", "")),
        severity=severity,
        risk_score=risk,
        cve_ids=list(raw.get("cve_ids", [])),
        compliance_frameworks=list(raw.get("compliance_frameworks", [])),
        affected_attribute=raw.get("affected_attribute"),
        evidence=raw.get("evidence"),
        tags=list(raw.get("tags", [])),
    )


def _parse_recommendation(raw: Dict[str, Any]) -> Recommendation:
    """Parse a raw dict into a ``Recommendation``, applying sensible defaults."""
    priority_str = str(raw.get("priority", "medium")).lower()
    try:
        priority = RemediationPriority(priority_str)
    except ValueError:
        priority = RemediationPriority.MEDIUM

    return Recommendation(
        id=str(raw.get("id", uuid.uuid4())),
        finding_ids=list(raw.get("finding_ids", [])),
        title=str(raw.get("title", "Unnamed Recommendation")),
        description=str(raw.get("description", "")),
        priority=priority,
        effort=str(raw.get("effort", "medium")).lower(),
        steps=list(raw.get("steps", [])),
        references=list(raw.get("references", [])),
        auto_remediable=bool(raw.get("auto_remediable", False)),
        automation_script=raw.get("automation_script"),
    )


# ---------------------------------------------------------------------------
# ResponseParser
# ---------------------------------------------------------------------------


class ResponseParser:
    """
    Parses raw LLM text responses into structured domain objects.

    Usage::

        parser = ResponseParser()
        result = parser.parse(request_id="req-1", resource_id="bucket-1", raw_text=llm_output)
    """

    def parse(
        self,
        request_id: str,
        resource_id: str,
        raw_text: str,
        resources_analysed: int = 1,
    ) -> AnalysisResult:
        """
        Parse the raw LLM response into an ``AnalysisResult``.

        Parameters
        ----------
        request_id:
            Correlating request identifier.
        resource_id:
            Default resource ID to use for findings that lack one.
        raw_text:
            Raw text output from the LLM.
        resources_analysed:
            Number of resources covered by this response.

        Returns
        -------
        AnalysisResult
            A fully validated analysis result.  If parsing fails, an
            ``AnalysisResult`` with an error summary is returned instead
            of raising an exception.
        """
        json_str = _extract_json(raw_text)

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as exc:
            return AnalysisResult(
                request_id=request_id,
                resources_analysed=resources_analysed,
                summary=f"Failed to parse AI response as JSON: {exc}. Raw: {raw_text[:500]}",
                metadata={"parse_error": str(exc), "raw_snippet": raw_text[:500]},
            )

        findings: List[Finding] = []
        for raw_finding in data.get("findings", []):
            try:
                findings.append(_parse_finding(raw_finding, resource_id))
            except Exception as exc:  # noqa: BLE001
                # Skip malformed findings rather than failing entirely
                findings.append(
                    Finding(
                        id=str(uuid.uuid4()),
                        resource_id=resource_id,
                        title="Malformed finding (parse error)",
                        description=str(exc),
                        severity=FindingSeverity.INFO,
                        risk_score=RiskScore(base_score=0.0),
                    )
                )

        recommendations: List[Recommendation] = []
        for raw_rec in data.get("recommendations", []):
            try:
                recommendations.append(_parse_recommendation(raw_rec))
            except Exception:  # noqa: BLE001
                pass

        return AnalysisResult(
            request_id=request_id,
            resources_analysed=resources_analysed,
            findings=findings,
            recommendations=recommendations,
            summary=str(data.get("summary", "")),
        )

    def parse_multiple(
        self,
        request_id: str,
        responses: List[Dict[str, str]],
    ) -> AnalysisResult:
        """
        Merge multiple per-resource LLM responses into a single AnalysisResult.

        Parameters
        ----------
        request_id:
            Correlating request identifier.
        responses:
            List of dicts with keys ``resource_id`` and ``raw_text``.
        """
        all_findings: List[Finding] = []
        all_recommendations: List[Recommendation] = []
        summaries: List[str] = []

        for resp in responses:
            partial = self.parse(
                request_id=request_id,
                resource_id=resp["resource_id"],
                raw_text=resp["raw_text"],
            )
            all_findings.extend(partial.findings)
            all_recommendations.extend(partial.recommendations)
            if partial.summary:
                summaries.append(partial.summary)

        merged_summary = " | ".join(summaries) if summaries else ""

        return AnalysisResult(
            request_id=request_id,
            resources_analysed=len(responses),
            findings=all_findings,
            recommendations=all_recommendations,
            summary=merged_summary,
        )


# ---------------------------------------------------------------------------
# ResponseFormatter — human-readable output
# ---------------------------------------------------------------------------

_SEVERITY_EMOJI: Dict[FindingSeverity, str] = {
    FindingSeverity.CRITICAL: "🔴",
    FindingSeverity.HIGH: "🟠",
    FindingSeverity.MEDIUM: "🟡",
    FindingSeverity.LOW: "🔵",
    FindingSeverity.INFO: "⚪",
}

_PRIORITY_EMOJI: Dict[RemediationPriority, str] = {
    RemediationPriority.IMMEDIATE: "🚨",
    RemediationPriority.HIGH: "🔴",
    RemediationPriority.MEDIUM: "🟡",
    RemediationPriority.LOW: "🔵",
    RemediationPriority.DEFERRED: "⚪",
}


class ResponseFormatter:
    """
    Formats ``AnalysisResult`` objects for human consumption.

    Supports plain-text CLI output and Markdown report generation.
    """

    # ------------------------------------------------------------------
    # Plain text
    # ------------------------------------------------------------------

    def to_text(self, result: AnalysisResult, verbose: bool = False) -> str:
        """Render an ``AnalysisResult`` as plain text for CLI output."""
        lines: List[str] = []

        lines.append("=" * 70)
        lines.append("InfraMind AI — Analysis Report")
        lines.append(f"Request ID : {result.request_id}")
        lines.append(f"Generated  : {result.created_at.strftime('%Y-%m-%d %H:%M UTC')}")
        lines.append(f"Resources  : {result.resources_analysed}")
        if result.overall_risk_score is not None:
            lines.append(f"Risk Score : {result.overall_risk_score:.1f} / 10.0")
        lines.append("=" * 70)

        if result.summary:
            lines.append("\nEXECUTIVE SUMMARY")
            lines.append("-" * 40)
            lines.append(result.summary)

        lines.append(f"\nFINDINGS ({len(result.findings)})")
        lines.append("-" * 40)
        for finding in sorted(
            result.findings,
            key=lambda f: f.risk_score.overall_score or 0,
            reverse=True,
        ):
            emoji = _SEVERITY_EMOJI.get(finding.severity, "")
            lines.append(
                f"{emoji} [{finding.severity.value.upper()}] {finding.title} "
                f"(score: {finding.risk_score.overall_score:.1f})"
            )
            if verbose:
                lines.append(f"   Resource : {finding.resource_id}")
                lines.append(f"   {finding.description}")
                if finding.affected_attribute:
                    lines.append(f"   Attribute: {finding.affected_attribute}")
                if finding.compliance_frameworks:
                    lines.append(f"   Compliance: {', '.join(finding.compliance_frameworks)}")
                lines.append("")

        lines.append(f"\nRECOMMENDATIONS ({len(result.recommendations)})")
        lines.append("-" * 40)
        for rec in sorted(
            result.recommendations,
            key=lambda r: list(RemediationPriority).index(r.priority),
        ):
            emoji = _PRIORITY_EMOJI.get(rec.priority, "")
            lines.append(f"{emoji} [{rec.priority.value.upper()}] {rec.title}")
            if verbose and rec.steps:
                for i, step in enumerate(rec.steps, 1):
                    lines.append(f"   {i}. {step}")
                lines.append("")

        lines.append("=" * 70)
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Markdown
    # ------------------------------------------------------------------

    def to_markdown(self, result: AnalysisResult) -> str:
        """Render an ``AnalysisResult`` as a Markdown report."""
        lines: List[str] = []

        lines.append("# InfraMind AI — Analysis Report\n")
        lines.append(f"| Field | Value |")
        lines.append(f"|---|---|")
        lines.append(f"| Request ID | `{result.request_id}` |")
        lines.append(f"| Generated | {result.created_at.strftime('%Y-%m-%d %H:%M UTC')} |")
        lines.append(f"| Resources analysed | {result.resources_analysed} |")
        if result.overall_risk_score is not None:
            lines.append(f"| Overall risk score | **{result.overall_risk_score:.1f} / 10.0** |")
        lines.append("")

        if result.summary:
            lines.append("## Executive Summary\n")
            lines.append(result.summary)
            lines.append("")

        lines.append(f"## Findings ({len(result.findings)})\n")
        if result.findings:
            lines.append("| Severity | Title | Score | Resource |")
            lines.append("|---|---|---|---|")
            for finding in sorted(
                result.findings,
                key=lambda f: f.risk_score.overall_score or 0,
                reverse=True,
            ):
                emoji = _SEVERITY_EMOJI.get(finding.severity, "")
                score = f"{finding.risk_score.overall_score:.1f}" if finding.risk_score.overall_score is not None else "—"
                lines.append(
                    f"| {emoji} {finding.severity.value.upper()} "
                    f"| {finding.title} | {score} | `{finding.resource_id}` |"
                )
            lines.append("")

            for finding in sorted(
                result.findings,
                key=lambda f: f.risk_score.overall_score or 0,
                reverse=True,
            ):
                emoji = _SEVERITY_EMOJI.get(finding.severity, "")
                lines.append(f"### {emoji} {finding.title}\n")
                lines.append(f"**Severity:** {finding.severity.value.upper()}  ")
                score = f"{finding.risk_score.overall_score:.1f}" if finding.risk_score.overall_score is not None else "—"
                lines.append(f"**Score:** {score}  ")
                lines.append(f"**Resource:** `{finding.resource_id}`\n")
                lines.append(finding.description)
                if finding.affected_attribute:
                    lines.append(f"\n**Affected attribute:** `{finding.affected_attribute}`")
                if finding.evidence:
                    lines.append(f"\n**Evidence:**\n```\n{finding.evidence}\n```")
                if finding.cve_ids:
                    lines.append(f"\n**CVEs:** {', '.join(finding.cve_ids)}")
                if finding.compliance_frameworks:
                    lines.append(f"\n**Compliance:** {', '.join(finding.compliance_frameworks)}")
                lines.append("")
        else:
            lines.append("_No findings reported._\n")

        lines.append(f"## Recommendations ({len(result.recommendations)})\n")
        if result.recommendations:
            for rec in sorted(
                result.recommendations,
                key=lambda r: list(RemediationPriority).index(r.priority),
            ):
                emoji = _PRIORITY_EMOJI.get(rec.priority, "")
                lines.append(f"### {emoji} {rec.title}\n")
                lines.append(f"**Priority:** {rec.priority.value.upper()}  ")
                lines.append(f"**Effort:** {rec.effort}\n")
                lines.append(rec.description)
                if rec.steps:
                    lines.append("\n**Steps:**")
                    for i, step in enumerate(rec.steps, 1):
                        lines.append(f"{i}. {step}")
                if rec.references:
                    lines.append("\n**References:**")
                    for ref in rec.references:
                        lines.append(f"- {ref}")
                if rec.automation_script:
                    lines.append(f"\n**Automation:**\n```bash\n{rec.automation_script}\n```")
                lines.append("")
        else:
            lines.append("_No recommendations._\n")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # JSON export
    # ------------------------------------------------------------------

    def to_json(self, result: AnalysisResult, indent: int = 2) -> str:
        """Serialise an ``AnalysisResult`` to a JSON string."""
        return result.model_dump_json(indent=indent)
