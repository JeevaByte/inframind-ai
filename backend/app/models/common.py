from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class InfraFileType(str, Enum):
    TERRAFORM = "terraform"
    CLOUDFORMATION = "cloudformation"
    KUBERNETES = "kubernetes"
    DOCKERFILE = "dockerfile"
    ANSIBLE = "ansible"
    UNKNOWN = "unknown"


class AnalysisType(str, Enum):
    SECURITY = "security"
    COST = "cost"
    COMPLIANCE = "compliance"
    FULL = "full"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Generic response envelope
# ---------------------------------------------------------------------------

DataT = TypeVar("DataT")


class APIResponse(BaseModel, Generic[DataT]):
    success: bool = True
    data: Optional[DataT] = None
    message: Optional[str] = None
    errors: Optional[List[str]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"arbitrary_types_allowed": True}


class PaginatedResponse(BaseModel, Generic[DataT]):
    items: List[DataT]
    total: int
    page: int = 1
    page_size: int = 20
    has_next: bool = False
    has_prev: bool = False


# ---------------------------------------------------------------------------
# Finding / Issue
# ---------------------------------------------------------------------------


class Finding(BaseModel):
    id: str
    rule_id: str
    title: str
    description: str
    severity: Severity
    resource: Optional[str] = None
    line_number: Optional[int] = None
    recommendation: str
    references: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# File metadata
# ---------------------------------------------------------------------------


class UploadedFile(BaseModel):
    file_id: UUID
    filename: str
    original_filename: str
    file_type: InfraFileType
    size_bytes: int
    content_type: str
    uploaded_at: datetime
    checksum: str


# ---------------------------------------------------------------------------
# Analysis result
# ---------------------------------------------------------------------------


class AnalysisResult(BaseModel):
    analysis_id: UUID
    file_id: UUID
    analysis_type: AnalysisType
    status: AnalysisStatus
    findings: List[Finding] = Field(default_factory=list)
    summary: Optional[str] = None
    score: Optional[float] = Field(default=None, ge=0, le=100)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
