"""
AI services for InfraMind — the authoritative AI module.

This package contains all AI-related logic:
  - analysis_service  : orchestrates file analysis end-to-end
  - infra_parser      : extracts structured context from infrastructure files
  - prompt_builder    : assembles prompts for the OpenAI API
  - openai_client     : thin wrapper around the OpenAI API
  - response_parser   : normalises raw model output into findings
  - scoring           : computes risk / quality scores from findings
"""

from app.services.ai.analysis_service import AIAnalysisService

__all__ = ["AIAnalysisService"]