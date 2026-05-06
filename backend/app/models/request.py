from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.common import AnalysisType


class AnalysisRequestBody(BaseModel):
    """Request body for triggering analysis on an already-uploaded file."""

    analysis_type: AnalysisType = AnalysisType.FULL
    options: Optional[dict] = Field(default_factory=dict)


class BulkAnalysisRequestBody(BaseModel):
    """Trigger analysis on multiple files at once."""

    file_ids: List[str] = Field(..., min_length=1, max_length=20)
    analysis_type: AnalysisType = AnalysisType.FULL
    options: Optional[dict] = Field(default_factory=dict)
