from __future__ import annotations

import hashlib
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import aiofiles
from fastapi import UploadFile

from app.config import Settings, get_settings
from app.models.common import InfraFileType, UploadedFile
from app.utils.validators import validate_file

logger = logging.getLogger(__name__)

# In-memory registry (replace with a database in production)
_file_registry: Dict[str, UploadedFile] = {}


def _detect_file_type(filename: str, content: bytes) -> InfraFileType:
    name_lower = filename.lower()

    if "dockerfile" in name_lower:
        return InfraFileType.DOCKERFILE
    if name_lower.endswith((".tf", ".tfvars", ".hcl")):
        return InfraFileType.TERRAFORM
    if name_lower.endswith((".yaml", ".yml")):
        # Heuristic: look for CloudFormation / Kubernetes markers
        text = content.decode("utf-8", errors="ignore")
        if all(marker in text for marker in ["on:", "jobs:"]):
            return InfraFileType.GITHUB_ACTIONS
        if "AWSTemplateFormatVersion" in text or "Resources:" in text:
            return InfraFileType.CLOUDFORMATION
        if "apiVersion" in text and "kind" in text:
            return InfraFileType.KUBERNETES
        if "hosts:" in text or "tasks:" in text:
            return InfraFileType.ANSIBLE
        return InfraFileType.UNKNOWN
    if name_lower.endswith(".json"):
        text = content.decode("utf-8", errors="ignore")
        if "AWSTemplateFormatVersion" in text or '"Resources"' in text:
            return InfraFileType.CLOUDFORMATION
        return InfraFileType.UNKNOWN
    if name_lower.endswith(".template"):
        return InfraFileType.CLOUDFORMATION

    return InfraFileType.UNKNOWN


class FileService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._upload_dir = Path(settings.upload_dir)

    async def save_upload(self, upload: UploadFile) -> UploadedFile:
        content = await upload.read()

        # Validate size & extension
        validate_file(
            filename=upload.filename or "",
            content=content,
            allowed_extensions=self._settings.allowed_extensions_list,
            max_size_bytes=self._settings.max_file_size_bytes,
        )

        file_id = uuid.uuid4()
        extension = Path(upload.filename or "").suffix
        stored_filename = f"{file_id}{extension}"
        dest_path = self._upload_dir / stored_filename

        async with aiofiles.open(dest_path, "wb") as out_file:
            await out_file.write(content)

        checksum = hashlib.sha256(content).hexdigest()
        file_type = _detect_file_type(upload.filename or "", content)

        record = UploadedFile(
            file_id=file_id,
            filename=stored_filename,
            original_filename=upload.filename or stored_filename,
            file_type=file_type,
            size_bytes=len(content),
            content_type=upload.content_type or "application/octet-stream",
            uploaded_at=datetime.now(timezone.utc),
            checksum=checksum,
        )
        _file_registry[str(file_id)] = record
        logger.info("Saved file %s as %s (%s)", upload.filename, stored_filename, file_type)
        return record

    async def list_files(self) -> List[UploadedFile]:
        return list(_file_registry.values())

    async def get_file_metadata(self, file_id: uuid.UUID) -> Optional[UploadedFile]:
        return _file_registry.get(str(file_id))

    async def get_file_path(self, file_id: uuid.UUID) -> Optional[Tuple[str, str]]:
        record = _file_registry.get(str(file_id))
        if not record:
            return None
        path = str(self._upload_dir / record.filename)
        return path, record.original_filename

    async def delete_file(self, file_id: uuid.UUID) -> bool:
        record = _file_registry.pop(str(file_id), None)
        if not record:
            return False
        path = self._upload_dir / record.filename
        if path.exists():
            path.unlink()
        logger.info("Deleted file %s", record.filename)
        return True

    async def read_content(self, file_id: uuid.UUID) -> Optional[str]:
        record = _file_registry.get(str(file_id))
        if not record:
            return None
        path = self._upload_dir / record.filename
        async with aiofiles.open(path, "r", errors="replace") as f:
            return await f.read()


def get_file_service() -> FileService:
    return FileService(get_settings())
