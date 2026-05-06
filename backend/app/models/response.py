from __future__ import annotations

from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.common import AnalysisResult, AnalysisStatus, AnalysisType, UploadedFile


class FileUploadResponse(BaseModel):
    file_id: UUID
    filename: str
    file_type: str
    size_bytes: int
    message: str = "File uploaded successfully"


class FileListResponse(BaseModel):
    files: List[UploadedFile]
    total: int


class AnalysisResponse(BaseModel):
    analysis_id: UUID
    file_id: UUID
    status: AnalysisStatus
    analysis_type: AnalysisType
    message: str = "Analysis started"


class AnalysisSummaryResponse(BaseModel):
    analysis_id: UUID
    file_id: UUID
    status: AnalysisStatus
    total_findings: int = 0
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0
    score: Optional[float] = None
    summary: Optional[str] = None


class BulkAnalysisResponse(BaseModel):
    submitted: List[AnalysisResponse]
    failed: List[Dict[str, str]] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    environment: str
    services: Dict[str, str] = Field(default_factory=dict)
