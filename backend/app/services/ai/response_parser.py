from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from pydantic import BaseModel, Field, ValidationError, field_validator


class AIAnalysisFinding(BaseModel):
    title: str
    severity: str
    category: str
    description: str
    recommendation: str
    estimated_impact: str = ""

    @field_validator("severity", mode="before")
    @classmethod
    def normalize_severity(cls, value: Any) -> str:
        text = str(value or "medium").strip().lower()
        return text if text in {"critical", "high", "medium", "low"} else "medium"

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, value: Any) -> str:
        text = str(value or "compliance").strip().lower()
        allowed = {"security", "reliability", "cost", "compliance"}
        return text if text in allowed else "compliance"


class AIAnalysisPayload(BaseModel):
    summary: str = ""
    score: float = Field(default=0, ge=0, le=100)
    deployment_readiness: str = "Needs review"
    findings: List[AIAnalysisFinding] = Field(default_factory=list)
    architecture_summary: str = ""
    top_recommendations: List[str] = Field(default_factory=list)
    security_score: float | None = Field(default=None, ge=0, le=100)
    reliability_score: float | None = Field(default=None, ge=0, le=100)
    cost_optimization_score: float | None = Field(default=None, ge=0, le=100)
    compliance_score: float | None = Field(default=None, ge=0, le=100)


class AIResponseParser:
    def parse(self, payload: str | Dict[str, Any]) -> AIAnalysisPayload:
        data = payload if isinstance(payload, dict) else self._extract_json(payload)
        try:
            parsed = AIAnalysisPayload.model_validate(data)
        except ValidationError as exc:
            raise ValueError(f"AI response did not match the expected schema: {exc}") from exc

        if not parsed.top_recommendations:
            parsed.top_recommendations = [
                finding.recommendation for finding in parsed.findings[:3] if finding.recommendation
            ]
        return parsed

    def _extract_json(self, raw_text: str) -> Dict[str, Any]:
        raw_text = raw_text.strip()
        if raw_text.startswith("```"):
            fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw_text, re.DOTALL)
            if fenced:
                raw_text = fenced.group(1)

        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            match = re.search(r"(\{.*\})", raw_text, re.DOTALL)
            if not match:
                raise ValueError("AI response did not contain valid JSON.")
            return json.loads(match.group(1))