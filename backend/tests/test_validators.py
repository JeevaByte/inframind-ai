from __future__ import annotations

import pytest

from app.utils.validators import sanitize_filename, validate_file


ALLOWED = ["tf", "tfvars", "json", "yaml", "yml", "hcl", "template", "dockerfile"]
MAX_BYTES = 10 * 1024 * 1024  # 10 MB


class TestValidateFile:
    def test_valid_tf_file(self):
        validate_file("main.tf", b"# terraform", ALLOWED, MAX_BYTES)

    def test_valid_dockerfile(self):
        validate_file("Dockerfile", b"FROM python:3.12", ALLOWED, MAX_BYTES)

    def test_rejects_empty_content(self):
        with pytest.raises(ValueError, match="empty"):
            validate_file("main.tf", b"", ALLOWED, MAX_BYTES)

    def test_rejects_disallowed_extension(self):
        with pytest.raises(ValueError, match="not allowed"):
            validate_file("script.py", b"print('hi')", ALLOWED, MAX_BYTES)

    def test_rejects_oversized_file(self):
        with pytest.raises(ValueError, match="maximum allowed size"):
            validate_file("big.tf", b"x" * (MAX_BYTES + 1), ALLOWED, MAX_BYTES)

    def test_rejects_empty_filename(self):
        with pytest.raises(ValueError, match="Filename"):
            validate_file("", b"content", ALLOWED, MAX_BYTES)

    def test_rejects_no_extension(self):
        with pytest.raises(ValueError, match="no extension"):
            validate_file("Makefile", b"all:", ALLOWED, MAX_BYTES)


class TestSanitizeFilename:
    def test_strips_path_traversal(self):
        assert sanitize_filename("../../etc/passwd") == "passwd"

    def test_strips_windows_path(self):
        assert sanitize_filename("C:\\Windows\\System32\\cmd.exe") == "cmd.exe"

    def test_plain_filename_unchanged(self):
        assert sanitize_filename("main.tf") == "main.tf"
