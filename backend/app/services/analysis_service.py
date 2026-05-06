from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.config import Settings, get_settings
from app.models.common import AnalysisResult, AnalysisStatus, AnalysisType
from app.services.ai.analysis_service import AIAnalysisService
from app.services.file_service import FileService, get_file_service

logger = logging.getLogger(__name__)

# In-memory store (replace with a database in production)
_analysis_store: Dict[str, AnalysisResult] = {}


class AnalysisService:
    def __init__(self, settings: Settings, file_service: FileService) -> None:
        self._settings = settings
        self._file_service = file_service
        self._ai = AIAnalysisService(settings)

    async def start_analysis(
        self,
        file_id: uuid.UUID,
        analysis_type: AnalysisType,
        options: Dict[str, Any],
    ) -> AnalysisResult:
        file_meta = await self._file_service.get_file_metadata(file_id)
        if not file_meta:
            raise FileNotFoundError(f"File {file_id} not found.")

        analysis_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        result = AnalysisResult(
            analysis_id=analysis_id,
            file_id=file_id,
            analysis_type=analysis_type,
            status=AnalysisStatus.RUNNING,
            started_at=now,
        )
        _analysis_store[str(analysis_id)] = result

        # Run analysis synchronously for the mock (in production: dispatch to a task queue)
        try:
            content = await self._file_service.read_content(file_id)
            ai_result = await self._ai.analyze(
                content=content or "",
                filename=file_meta.original_filename,
                file_type=file_meta.file_type,
                analysis_type=analysis_type,
                options=options,
            )
            result.findings = ai_result["findings"]
            result.summary = ai_result["summary"]
            result.score = ai_result["score"]
            result.security_score = ai_result["security_score"]
            result.reliability_score = ai_result["reliability_score"]
            result.cost_optimization_score = ai_result["cost_optimization_score"]
            result.compliance_score = ai_result["compliance_score"]
            result.deployment_readiness = ai_result["deployment_readiness"]
            result.architecture_summary = ai_result["architecture_summary"]
            result.top_recommendations = ai_result["top_recommendations"]
            result.metadata = ai_result["metadata"]
            result.status = AnalysisStatus.COMPLETED
            result.completed_at = datetime.now(timezone.utc)
        except Exception as exc:
            logger.exception("Analysis %s failed: %s", analysis_id, exc)
            result.status = AnalysisStatus.FAILED
            result.error_message = str(exc)
            result.completed_at = datetime.now(timezone.utc)

        _analysis_store[str(analysis_id)] = result
        logger.info(
            "Analysis %s (%s) finished with status %s, %d findings",
            analysis_id,
            analysis_type,
            result.status,
            len(result.findings),
        )
        return result

    async def get_result(self, analysis_id: uuid.UUID) -> Optional[AnalysisResult]:
        return _analysis_store.get(str(analysis_id))

    async def list_results_for_file(self, file_id: uuid.UUID) -> List[AnalysisResult]:
        return [r for r in _analysis_store.values() if r.file_id == file_id]


def get_analysis_service() -> AnalysisService:
    settings = get_settings()
    file_service = get_file_service()
    return AnalysisService(settings, file_service)
