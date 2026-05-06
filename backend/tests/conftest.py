from __future__ import annotations

import os
import tempfile

import pytest
from fastapi.testclient import TestClient

import app.services.file_service as file_svc
import app.services.analysis_service as analysis_svc
from app.config import get_settings


@pytest.fixture(autouse=True)
def isolated_stores(tmp_path, monkeypatch):
    """Give each test a clean upload dir and empty in-memory stores."""
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()

    # Patch the settings to use tmp upload dir
    settings = get_settings()
    monkeypatch.setattr(settings, "upload_dir", str(upload_dir))

    # Clear in-memory registries between tests
    file_svc._file_registry.clear()
    analysis_svc._analysis_store.clear()

    yield

    file_svc._file_registry.clear()
    analysis_svc._analysis_store.clear()
