"""SARIF 2.1.0 output for infralint findings."""

from __future__ import annotations

from typing import Any, Iterable

from . import __version__

_SEVERITY_TO_LEVEL = {
    "critical": "error",
    "high": "error",
    "medium": "warning",
    "low": "note",
    "info": "note",
}


def to_sarif(findings: Iterable[dict[str, Any]], *, tool_uri: str | None = None) -> dict[str, Any]:
    """Convert infralint findings into a SARIF 2.1.0 log."""
    materialized = list(findings)
    rules: dict[str, dict[str, Any]] = {}
    results: list[dict[str, Any]] = []

    for finding in materialized:
        rule_id = finding.get("rule_id") or finding.get("id") or "INFRALINT-UNK-000"
        severity = str(finding.get("severity") or "info").lower()
        level = _SEVERITY_TO_LEVEL.get(severity, "note")

        if rule_id not in rules:
            title = finding.get("title", rule_id)
            category = finding.get("category", "security")
            rules[rule_id] = {
                "id": rule_id,
                "name": title,
                "shortDescription": {"text": title},
                "fullDescription": {"text": finding.get("description", "")},
                "helpUri": tool_uri or "https://github.com/JeevaByte/inframind-ai",
                "properties": {
                    "category": category,
                    "tags": [category],
                },
                "defaultConfiguration": {"level": level},
            }

        location: dict[str, Any] = {
            "physicalLocation": {
                "artifactLocation": {"uri": finding.get("file", "unknown")},
            }
        }
        line = finding.get("line") or finding.get("line_number")
        if line:
            location["physicalLocation"]["region"] = {"startLine": int(line)}

        results.append({
            "ruleId": rule_id,
            "level": level,
            "message": {"text": finding.get("description") or finding.get("title", rule_id)},
            "locations": [location],
            "properties": {
                "severity": severity,
                "recommendation": finding.get("recommendation", ""),
            },
        })

    return {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {
                "driver": {
                    "name": "infralint",
                    "version": __version__,
                    "informationUri": tool_uri or "https://github.com/JeevaByte/inframind-ai",
                    "rules": list(rules.values()),
                }
            },
            "results": results,
        }],
    }