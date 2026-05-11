"""File-type detection from path and content sniffing."""

from __future__ import annotations

from pathlib import Path

TERRAFORM = "terraform"
KUBERNETES = "kubernetes"
CLOUDFORMATION = "cloudformation"
DOCKERFILE = "dockerfile"
GITHUB_ACTIONS = "github_actions"
UNKNOWN = "unknown"

_TF_SUFFIXES = {".tf", ".tf.json", ".tfvars"}
_YAML_SUFFIXES = {".yaml", ".yml"}
_JSON_SUFFIXES = {".json"}


def detect(path: Path) -> str:
    """Return the infralint file-type identifier for a given path."""
    name = path.name
    lower_name = name.lower()
    suffix = "".join(path.suffixes).lower()

    if lower_name == "dockerfile" or lower_name.startswith("dockerfile.") or suffix == ".dockerfile":
        return DOCKERFILE

    if suffix in _TF_SUFFIXES or path.suffix.lower() == ".tf":
        return TERRAFORM

    parts_lower = {part.lower() for part in path.parts}
    if ".github" in parts_lower and "workflows" in parts_lower and path.suffix.lower() in _YAML_SUFFIXES:
        return GITHUB_ACTIONS

    if path.suffix.lower() in _YAML_SUFFIXES | _JSON_SUFFIXES:
        try:
            head = path.read_text(encoding="utf-8", errors="ignore")[:4096].lower()
        except OSError:
            return UNKNOWN
        if "awstemplateformatversion" in head or ('"resources"' in head and "aws::" in head):
            return CLOUDFORMATION
        if "apiversion:" in head and "kind:" in head:
            return KUBERNETES
        if "aws::" in head:
            return CLOUDFORMATION

    return UNKNOWN


def is_supported(path: Path) -> bool:
    return detect(path) != UNKNOWN