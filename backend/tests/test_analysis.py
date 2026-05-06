from __future__ import annotations

import io
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

_VULNERABLE_TF = """
resource "aws_security_group" "open" {
  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_instance" "main" {
  password  = "supersecretpassword123"
  encrypted = false
  tags = {}
}
"""

_CLEAN_TF = """
resource "aws_s3_bucket" "safe" {
  bucket = "my-safe-bucket"
  tags = {
    Owner       = "platform-team"
    Environment = "production"
  }
}
"""


def _upload_tf(content: str, name: str = "infra.tf") -> str:
    r = client.post(
        "/api/v1/files/upload",
        files={"file": (name, io.BytesIO(content.encode()), "text/plain")},
    )
    assert r.status_code == 201
    return r.json()["data"]["file_id"]


class TestAnalysisEndpoints:
    def test_trigger_security_analysis(self):
        file_id = _upload_tf(_VULNERABLE_TF)
        r = client.post(f"/api/v1/analysis/{file_id}", json={"analysis_type": "security"})
        assert r.status_code == 202
        body = r.json()
        assert body["success"] is True
        assert body["data"]["status"] in ("completed", "running")

    def test_get_analysis_result_with_findings(self):
        file_id = _upload_tf(_VULNERABLE_TF)
        post_r = client.post(f"/api/v1/analysis/{file_id}", json={"analysis_type": "full"})
        analysis_id = post_r.json()["data"]["analysis_id"]

        r = client.get(f"/api/v1/analysis/{analysis_id}")
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["analysis_id"] == analysis_id
        # The vulnerable file should have at least one finding
        assert len(data["findings"]) > 0

    def test_get_analysis_summary(self):
        file_id = _upload_tf(_VULNERABLE_TF)
        post_r = client.post(f"/api/v1/analysis/{file_id}", json={"analysis_type": "full"})
        analysis_id = post_r.json()["data"]["analysis_id"]

        r = client.get(f"/api/v1/analysis/{analysis_id}/summary")
        assert r.status_code == 200
        summary = r.json()["data"]
        assert summary["total_findings"] >= 0
        assert "score" in summary
        assert "deployment_readiness" in summary

    def test_full_analysis_includes_ai_metadata(self):
        file_id = _upload_tf(_VULNERABLE_TF, "ai-demo.tf")
        post_r = client.post(f"/api/v1/analysis/{file_id}", json={"analysis_type": "full"})
        analysis_id = post_r.json()["data"]["analysis_id"]

        r = client.get(f"/api/v1/analysis/{analysis_id}")
        assert r.status_code == 200
        data = r.json()["data"]
        assert "deployment_readiness" in data
        assert "architecture_summary" in data
        assert "top_recommendations" in data
        assert "security_score" in data

    def test_clean_file_gets_perfect_score(self):
        file_id = _upload_tf(_CLEAN_TF, "clean.tf")
        post_r = client.post(f"/api/v1/analysis/{file_id}", json={"analysis_type": "security"})
        analysis_id = post_r.json()["data"]["analysis_id"]

        r = client.get(f"/api/v1/analysis/{analysis_id}")
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["score"] == 100.0

    def test_list_analyses_for_file(self):
        file_id = _upload_tf(_VULNERABLE_TF, "multi.tf")
        client.post(f"/api/v1/analysis/{file_id}", json={"analysis_type": "security"})
        client.post(f"/api/v1/analysis/{file_id}", json={"analysis_type": "cost"})

        r = client.get(f"/api/v1/analysis/file/{file_id}")
        assert r.status_code == 200
        assert len(r.json()["data"]) >= 2

    def test_analysis_for_nonexistent_file_returns_404(self):
        fake_id = str(uuid.uuid4())
        r = client.post(f"/api/v1/analysis/{fake_id}", json={"analysis_type": "security"})
        assert r.status_code == 404

    def test_get_nonexistent_analysis_returns_404(self):
        fake_id = str(uuid.uuid4())
        r = client.get(f"/api/v1/analysis/{fake_id}")
        assert r.status_code == 404

    def test_bulk_analysis(self):
        fid1 = _upload_tf(_VULNERABLE_TF, "bulk1.tf")
        fid2 = _upload_tf(_CLEAN_TF, "bulk2.tf")
        r = client.post(
            "/api/v1/analysis/bulk",
            json={"file_ids": [fid1, fid2], "analysis_type": "security"},
        )
        assert r.status_code == 202
        assert len(r.json()["data"]["submitted"]) == 2
