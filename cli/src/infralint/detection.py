"""File-type detection for infralint."""
from __future__ import annotations

import re
from pathlib import Path


_GITHUB_ACTIONS_RE = re.compile(r"\.github[\\/]workflows[\\/].+\.ya?ml$", re.IGNORECASE)


def detect(path: Path) -> str:
    """Return a lowercase string identifying the infrastructure file type."""
    name = path.name.lower()
    suffix = path.suffix.lower()

    if name == "dockerfile" or name.startswith("dockerfile."):
        return "dockerfile"

    if _GITHUB_ACTIONS_RE.search(str(path)):
        return "github_actions"

    if suffix in (".tf", ".tfvars"):
        return "terraform"

    if suffix in (".yaml", ".yml"):
        # Heuristic: look for Kubernetes / CloudFormation markers in the name
        if any(k in name for k in ("kubernetes", "k8s", "deploy", "service", "ingress", "pod", "statefulset", "daemonset")):
            return "kubernetes"
        return "yaml"

    if suffix == ".json":
        return "cloudformation"

    return "unknown"
