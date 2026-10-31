from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from starlette.concurrency import run_in_threadpool

from app.models.common import APIResponse
from app.models.fieldready import FieldReadyRequest, FieldReadyResponse
from app.services.fieldready_service import FieldReadyService, get_fieldready_service

router = APIRouter(prefix="/api/v1/fieldready", tags=["FieldReady"])


@router.post(
    "/advice",
    response_model=APIResponse[FieldReadyResponse],
    summary="Get a sourced weather update for a farm field",
    description=(
        "Pilot for corn and soybean fields in the contiguous United States. "
        "Coordinates are used for this request only and are not stored."
    ),
)
async def get_field_advice(
    request: FieldReadyRequest,
    service: FieldReadyService = Depends(get_fieldready_service),
) -> APIResponse[FieldReadyResponse]:
    try:
        result = await run_in_threadpool(service.advise, request)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return APIResponse(data=result)
