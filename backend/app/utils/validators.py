from __future__ import annotations

import os
from pathlib import Path
from typing import List

# Filenames that have no extension but are valid infrastructure files
_EXTENSION_LESS_ALLOWLIST = {"dockerfile"}


def validate_file(
    filename: str,
    content: bytes,
    allowed_extensions: List[str],
    max_size_bytes: int,
) -> None:
    """Validate uploaded file size and extension.

    Raises:
        ValueError: if validation fails (caller should convert to HTTP 422).
    """
    if not filename:
        raise ValueError("Filename must not be empty.")

    if len(content) == 0:
        raise ValueError("Uploaded file is empty.")

    if len(content) > max_size_bytes:
        mb = max_size_bytes / (1024 * 1024)
        raise ValueError(f"File exceeds the maximum allowed size of {mb:.0f} MB.")

    _validate_extension(filename, allowed_extensions)


def _validate_extension(filename: str, allowed_extensions: List[str]) -> None:
    name_lower = filename.lower()

    # Allow extension-less filenames that are in the allowlist (e.g. Dockerfile)
    stem = Path(filename).stem.lower()
    if stem in _EXTENSION_LESS_ALLOWLIST:
        return

    suffix = Path(filename).suffix.lstrip(".")
    if not suffix:
        raise ValueError(
            f"File '{filename}' has no extension. "
            f"Allowed extensions: {', '.join(allowed_extensions)}."
        )

    if suffix.lower() not in [ext.lower() for ext in allowed_extensions]:
        raise ValueError(
            f"File extension '.{suffix}' is not allowed. "
            f"Allowed extensions: {', '.join(allowed_extensions)}."
        )


def sanitize_filename(filename: str) -> str:
    """Strip directory traversal components and return only the base filename."""
    return os.path.basename(filename.replace("\\", "/"))
