from __future__ import annotations

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.models.common import APIResponse, UploadedFile
from app.models.response import FileListResponse, FileUploadResponse
from app.services.file_service import FileService, get_file_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/files", tags=["files"])


@router.post(
    "/upload",
    response_model=APIResponse[FileUploadResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload a single infrastructure file",
    description=(
        "Upload a single infrastructure configuration file (Terraform, "
        "CloudFormation, Kubernetes, Dockerfile, Ansible, …). "
        "The file is validated, stored, and a file record is returned."
    ),
)
async def upload_file(
    file: UploadFile = File(..., description="Infrastructure file to upload"),
    service: FileService = Depends(get_file_service),
) -> APIResponse[FileUploadResponse]:
    try:
        uploaded = await service.save_upload(file)
        return APIResponse(
            data=FileUploadResponse(
                file_id=uploaded.file_id,
                filename=uploaded.filename,
                file_type=uploaded.file_type.value,
                size_bytes=uploaded.size_bytes,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post(
    "/upload/bulk",
    response_model=APIResponse[List[FileUploadResponse]],
    status_code=status.HTTP_201_CREATED,
    summary="Upload multiple infrastructure files",
    description="Upload up to 20 infrastructure files in a single request.",
)
async def upload_files_bulk(
    files: List[UploadFile] = File(..., description="Infrastructure files to upload"),
    service: FileService = Depends(get_file_service),
) -> APIResponse[List[FileUploadResponse]]:
    if len(files) > 20:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot upload more than 20 files at once.",
        )

    results: List[FileUploadResponse] = []
    errors: List[str] = []

    for upload in files:
        try:
            uploaded = await service.save_upload(upload)
            results.append(
                FileUploadResponse(
                    file_id=uploaded.file_id,
                    filename=uploaded.filename,
                    file_type=uploaded.file_type.value,
                    size_bytes=uploaded.size_bytes,
                )
            )
        except ValueError as exc:
            errors.append(f"{upload.filename}: {exc}")

    return APIResponse(
        data=results,
        errors=errors if errors else None,
        success=len(errors) == 0,
    )


@router.get(
    "/",
    response_model=APIResponse[FileListResponse],
    summary="List uploaded files",
    description="Return a list of all previously uploaded infrastructure files.",
)
async def list_files(
    service: FileService = Depends(get_file_service),
) -> APIResponse[FileListResponse]:
    files = await service.list_files()
    return APIResponse(data=FileListResponse(files=files, total=len(files)))


@router.get(
    "/{file_id}",
    response_model=APIResponse[UploadedFile],
    summary="Get file metadata",
    description="Retrieve metadata for a specific uploaded file by its ID.",
)
async def get_file_metadata(
    file_id: UUID,
    service: FileService = Depends(get_file_service),
) -> APIResponse[UploadedFile]:
    file_meta = await service.get_file_metadata(file_id)
    if not file_meta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    return APIResponse(data=file_meta)


@router.get(
    "/{file_id}/download",
    summary="Download a file",
    description="Download the raw content of an uploaded infrastructure file.",
)
async def download_file(
    file_id: UUID,
    service: FileService = Depends(get_file_service),
) -> FileResponse:
    result = await service.get_file_path(file_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    path, original_name = result
    return FileResponse(path=path, filename=original_name)


@router.delete(
    "/{file_id}",
    response_model=APIResponse[None],
    summary="Delete an uploaded file",
    description="Permanently delete an uploaded file and its associated metadata.",
)
async def delete_file(
    file_id: UUID,
    service: FileService = Depends(get_file_service),
) -> APIResponse[None]:
    deleted = await service.delete_file(file_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    return APIResponse(message="File deleted successfully.")
