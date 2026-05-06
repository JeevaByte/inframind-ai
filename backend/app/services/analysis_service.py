from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.config import Settings, get_settings
from app.models.common import AnalysisResult, AnalysisStatus, AnalysisType
from app.services.file_service import FileService, get_file_service
from app.services.mock_ai_service import MockAIService

logger = logging.getLogger(__name__)

# In-memory store (replace with a database in production)
_analysis_store: Dict[str, AnalysisResult] = {}


class AnalysisService:
    def __init__(self, settings: Settings, file_service: FileService) -> None:
        self._settings = settings
        self._file_service = file_service
        self._ai = MockAIService()

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
        now = datetime.utcnow()

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
            findings, summary, score = await self._ai.analyze(
                content=content or "",
                file_type=file_meta.file_type,
                analysis_type=analysis_type,
                options=options,
            )
            result.findings = findings
            result.summary = summary
            result.score = score
            result.status = AnalysisStatus.COMPLETED
            result.completed_at = datetime.utcnow()
        except Exception as exc:
            logger.exception("Analysis %s failed: %s", analysis_id, exc)
            result.status = AnalysisStatus.FAILED
            result.error_message = str(exc)
            result.completed_at = datetime.utcnow()

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
