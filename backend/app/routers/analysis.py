from __future__ import annotations

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, status

from app.models.common import AnalysisResult, AnalysisType, APIResponse
from app.models.common import AnalysisResult, AnalysisType, APIResponse, Severity
from app.models.request import AnalysisRequestBody, BulkAnalysisRequestBody
from app.models.response import AnalysisResponse, AnalysisSummaryResponse, BulkAnalysisResponse
from app.services.analysis_service import AnalysisService, get_analysis_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])


@router.post(
    "/bulk",
    response_model=APIResponse[BulkAnalysisResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger analysis for multiple files",
    description="Submit analysis jobs for up to 20 files in a single request.",
)
async def trigger_bulk_analysis(
    body: BulkAnalysisRequestBody,
    service: AnalysisService = Depends(get_analysis_service),
) -> APIResponse[BulkAnalysisResponse]:
    submitted: List[AnalysisResponse] = []
    failed: List[dict] = []

    for fid_str in body.file_ids:
        try:
            fid = UUID(fid_str)
            result = await service.start_analysis(fid, body.analysis_type, body.options or {})
            submitted.append(
                AnalysisResponse(
                    analysis_id=result.analysis_id,
                    file_id=result.file_id,
                    status=result.status,
                    analysis_type=result.analysis_type,
                )
            )
        except (ValueError, FileNotFoundError) as exc:
            failed.append({"file_id": fid_str, "error": str(exc)})

    return APIResponse(
        data=BulkAnalysisResponse(submitted=submitted, failed=failed),
        success=len(failed) == 0,
    )


@router.post(
    "/{file_id}",
    response_model=APIResponse[AnalysisResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger analysis for a file",
    description=(
        "Start an analysis job for the specified infrastructure file. "
        "Supported analysis types: `security`, `reliability`, `cost`, `compliance`, `full`."
    ),
)
async def trigger_analysis(
    file_id: UUID,
    body: AnalysisRequestBody = Body(default_factory=AnalysisRequestBody),
    service: AnalysisService = Depends(get_analysis_service),
) -> APIResponse[AnalysisResponse]:
    try:
        result = await service.start_analysis(file_id, body.analysis_type, body.options or {})
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return APIResponse(
        data=AnalysisResponse(
            analysis_id=result.analysis_id,
            file_id=result.file_id,
            status=result.status,
            analysis_type=result.analysis_type,
        ),
        message="Analysis job submitted successfully.",
    )


@router.get(
    "/file/{file_id}",
    response_model=APIResponse[List[AnalysisResult]],
    summary="List all analyses for a file",
    description="Return all analysis jobs (completed, running, failed) for a given file ID.",
)
async def list_analyses_for_file(
    file_id: UUID,
    service: AnalysisService = Depends(get_analysis_service),
) -> APIResponse[List[AnalysisResult]]:
    results = await service.list_results_for_file(file_id)
    return APIResponse(data=results)


@router.get(
    "/{analysis_id}/summary",
    response_model=APIResponse[AnalysisSummaryResponse],
    summary="Get analysis summary",
    description="Retrieve a concise summary (finding counts per severity, overall score) for an analysis.",
)
async def get_analysis_summary(
    analysis_id: UUID,
    service: AnalysisService = Depends(get_analysis_service),
) -> APIResponse[AnalysisSummaryResponse]:
    result = await service.get_result(analysis_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found.")

    from app.models.common import Severity

    counts = {s: 0 for s in Severity}
    for finding in result.findings:
        counts[finding.severity] += 1

    return APIResponse(
        data=AnalysisSummaryResponse(
            analysis_id=result.analysis_id,
            file_id=result.file_id,
            status=result.status,
            total_findings=len(result.findings),
            critical=counts[Severity.CRITICAL],
            high=counts[Severity.HIGH],
            medium=counts[Severity.MEDIUM],
            low=counts[Severity.LOW],
            info=counts[Severity.INFO],
            score=result.score,
            security_score=result.security_score,
            reliability_score=result.reliability_score,
            cost_optimization_score=result.cost_optimization_score,
            compliance_score=result.compliance_score,
            deployment_readiness=result.deployment_readiness,
            summary=result.summary,
        )
    )


@router.get(
    "/{analysis_id}",
    response_model=APIResponse[AnalysisResult],
    summary="Get analysis result",
    description="Retrieve the full result of a completed (or in-progress) analysis job.",
)
async def get_analysis_result(
    analysis_id: UUID,
    service: AnalysisService = Depends(get_analysis_service),
) -> APIResponse[AnalysisResult]:
    result = await service.get_result(analysis_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found.")
    return APIResponse(data=result)
