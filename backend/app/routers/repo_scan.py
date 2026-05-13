from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.common import APIResponse
from app.models.repo_scan import RepoScanListResponse, RepoScanRequest, RepoScanResult
from app.services.repo_scan_service import RepoScanService, get_repo_scan_service

router = APIRouter(prefix="/api/v1/repo-scans", tags=["repo-scans"])


@router.post(
    "/",
    response_model=APIResponse[RepoScanResult],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger a repository security scan",
    description="Clone a GitHub repository and run the configured open-source security scanners.",
)
async def trigger_repo_scan(
    body: RepoScanRequest,
    service: RepoScanService = Depends(get_repo_scan_service),
) -> APIResponse[RepoScanResult]:
    result = await service.start_scan(body)
    if result.status == "failed" and not result.scanners:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=result.error_message or "Repository scan failed.")
    return APIResponse(data=result)


@router.get(
    "/",
    response_model=APIResponse[RepoScanListResponse],
    summary="List repository scans",
)
async def list_repo_scans(
    service: RepoScanService = Depends(get_repo_scan_service),
) -> APIResponse[RepoScanListResponse]:
    scans = await service.list_scans()
    return APIResponse(data=RepoScanListResponse(scans=scans, total=len(scans)))


@router.get(
    "/{scan_id}",
    response_model=APIResponse[RepoScanResult],
    summary="Get a repository scan result",
)
async def get_repo_scan(
    scan_id: UUID,
    service: RepoScanService = Depends(get_repo_scan_service),
) -> APIResponse[RepoScanResult]:
    result = await service.get_scan(scan_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository scan not found.")
    return APIResponse(data=result)
