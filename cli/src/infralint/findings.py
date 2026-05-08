"""Finding dataclass for infralint."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Finding:
    rule_id: str
    title: str
    severity: str
    category: str
    description: str
    recommendation: str
    file: str
    line: Optional[int] = None

    def as_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "title": self.title,
            "severity": self.severity,
            "category": self.category,
            "description": self.description,
            "recommendation": self.recommendation,
            "file": self.file,
            "line": self.line,
        }
