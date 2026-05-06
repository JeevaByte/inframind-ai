from __future__ import annotations

import json
from pathlib import Path

from app.models.common import AnalysisType
from app.services.ai.infra_parser import ParsedInfrastructureContext


class AIPromptBuilder:
    def __init__(self) -> None:
        self._prompt_root = Path(__file__).resolve().parents[3] / "prompts"

    def build(self, *, context: ParsedInfrastructureContext, analysis_type: AnalysisType) -> dict[str, str]:
        system_prompt = "\n\n".join(
            filter(
                None,
                [
                    self._read("system/reviewer.md"),
                    self._read("security/findings.md"),
                    self._read("scoring/readiness.md"),
                    self._read("explanations/architecture.md"),
                ],
            )
        )

        domain_template = {
            "terraform": self._read("terraform/context.md"),
            "kubernetes": self._read("kubernetes/context.md"),
        }.get(context.file_type.value, "")

        user_payload = {
            "analysis_type": analysis_type.value,
            "context": context.to_prompt_dict(),
            "instructions": {
                "return_json_only": True,
                "max_findings": 8,
                "required_schema": {
                    "summary": "string",
                    "score": "number 0-100",
                    "deployment_readiness": "string",
                    "findings": [
                        {
                            "title": "string",
                            "severity": "critical|high|medium|low",
                            "category": "security|cost|compliance|reliability",
                            "description": "string",
                            "recommendation": "string",
                            "estimated_impact": "string",
                        }
                    ],
                    "architecture_summary": "string",
                    "top_recommendations": ["string"],
                    "security_score": "number 0-100",
                    "reliability_score": "number 0-100",
                    "cost_optimization_score": "number 0-100",
                    "compliance_score": "number 0-100",
                },
            },
        }

        user_prompt = "\n\n".join(
            part for part in [domain_template, json.dumps(user_payload, indent=2)] if part
        )
        return {"system": system_prompt, "user": user_prompt}

    def _read(self, relative_path: str) -> str:
        path = self._prompt_root / relative_path
        return path.read_text(encoding="utf-8") if path.exists() else ""