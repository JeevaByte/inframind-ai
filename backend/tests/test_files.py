from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _upload(filename: str, content: str, content_type: str = "text/plain") -> dict:
    response = client.post(
        "/api/v1/files/upload",
        files={"file": (filename, io.BytesIO(content.encode()), content_type)},
    )
    return response


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        r = client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert "version" in body


class TestFileUpload:
    def test_upload_terraform_file(self):
        r = _upload("main.tf", 'resource "aws_instance" "example" {}')
        assert r.status_code == 201
        body = r.json()
        assert body["success"] is True
        assert body["data"]["file_type"] == "terraform"

    def test_upload_yaml_kubernetes_file(self):
        content = "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: my-app"
        r = _upload("deploy.yaml", content, "application/yaml")
        assert r.status_code == 201
        body = r.json()
        assert body["success"] is True
        assert body["data"]["file_type"] == "kubernetes"

    def test_upload_cloudformation_json(self):
        import json as _json

        cf = {"AWSTemplateFormatVersion": "2010-09-09", "Resources": {}}
        r = _upload("stack.json", _json.dumps(cf), "application/json")
        assert r.status_code == 201
        assert r.json()["data"]["file_type"] == "cloudformation"

    def test_upload_rejected_extension(self):
        r = _upload("malware.exe", b"\x00\x01\x02".decode("latin-1"), "application/octet-stream")
        assert r.status_code == 422

    def test_upload_empty_file(self):
        r = _upload("empty.tf", "")
        assert r.status_code == 422

    def test_list_files_returns_list(self):
        _upload("list_test.tf", "# test")
        r = client.get("/api/v1/files/")
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body["data"]["files"], list)

    def test_get_file_metadata(self):
        up = _upload("meta_test.tf", "# meta test")
        file_id = up.json()["data"]["file_id"]
        r = client.get(f"/api/v1/files/{file_id}")
        assert r.status_code == 200
        assert r.json()["data"]["file_id"] == file_id

    def test_get_nonexistent_file_returns_404(self):
        r = client.get("/api/v1/files/00000000-0000-0000-0000-000000000000")
        assert r.status_code == 404

    def test_delete_file(self):
        up = _upload("delete_me.tf", "# to delete")
        file_id = up.json()["data"]["file_id"]
        r = client.delete(f"/api/v1/files/{file_id}")
        assert r.status_code == 200
        # File should be gone
        r2 = client.get(f"/api/v1/files/{file_id}")
        assert r2.status_code == 404

    def test_bulk_upload(self):
        files = [
            ("files", ("a.tf", io.BytesIO(b"# a"), "text/plain")),
            ("files", ("b.tf", io.BytesIO(b"# b"), "text/plain")),
        ]
        r = client.post("/api/v1/files/upload/bulk", files=files)
        assert r.status_code == 201
        assert len(r.json()["data"]) == 2
