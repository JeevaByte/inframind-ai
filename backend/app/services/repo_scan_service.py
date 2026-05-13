from __future__ import annotations

import json
import logging
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID
from urllib.parse import quote

from app.config import Settings, get_settings
from app.models.common import AnalysisStatus, Finding, FindingCategory, Severity
from app.models.repo_scan import (
    RepoScanRequest,
    RepoScanResult,
    RepoScannerName,
    RepoScannerResult,
    summarize_findings,
)

logger = logging.getLogger(__name__)

_repo_scan_store: Dict[str, RepoScanResult] = {}


class RepoScanService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def start_scan(self, request: RepoScanRequest) -> RepoScanResult:
        scan = RepoScanResult(
            repository=request.repository,
            ref=request.ref,
            status=AnalysisStatus.RUNNING,
            metadata={"requested_scanners": [scanner.value for scanner in request.scanners]},
        )
        _repo_scan_store[str(scan.scan_id)] = scan

        workspace = Path(tempfile.mkdtemp(prefix="infralint-repo-scan-"))
        try:
            repo_path = self._clone_repository(request.repository, request.github_token, request.ref, workspace)
            scanners = [self._run_scanner(repo_path, scanner) for scanner in request.scanners]
            findings: List[Finding] = []
            for scanner_result in scanners:
                findings.extend(scanner_result.findings)

            scan.scanners = scanners
            scan.findings = findings
            scan.summary = summarize_findings(findings)
            scan.status = AnalysisStatus.COMPLETED if any(result.status == AnalysisStatus.COMPLETED for result in scanners) else AnalysisStatus.FAILED
            if scan.status == AnalysisStatus.FAILED:
                scan.error_message = "No configured scanners completed successfully."
            scan.metadata.update({
                "available_scanners": [result.scanner.value for result in scanners if result.error_message is None],
                "scanner_status": {result.scanner.value: result.status.value for result in scanners},
                "repository_path": str(repo_path),
                "used_github_token": bool(request.github_token),
            })
        except Exception as exc:
            logger.exception("Repository scan failed for %s: %s", request.repository, exc)
            scan.status = AnalysisStatus.FAILED
            scan.error_message = str(exc)
        finally:
            scan.completed_at = datetime.now(timezone.utc)
            _repo_scan_store[str(scan.scan_id)] = scan
            shutil.rmtree(workspace, ignore_errors=True)

        return scan

    async def get_scan(self, scan_id: UUID) -> Optional[RepoScanResult]:
        return _repo_scan_store.get(str(scan_id))

    async def list_scans(self) -> List[RepoScanResult]:
        return sorted(
            _repo_scan_store.values(),
            key=lambda scan: scan.started_at,
            reverse=True,
        )

    def _clone_repository(self, repository: str, github_token: Optional[str], ref: Optional[str], workspace: Path) -> Path:
        if not shutil.which("git"):
            raise RuntimeError("git is required to scan a repository but is not installed.")

        if "/" not in repository:
            raise RuntimeError("Repository must be provided as 'owner/name'.")

        destination = workspace / "repository"
        if github_token:
            encoded_token = quote(github_token, safe="")
            repo_url = f"https://x-access-token:{encoded_token}@github.com/{repository}.git"
        else:
            repo_url = f"https://github.com/{repository}.git"
        command = ["git", "clone", "--depth", "1"]
        if ref:
            command.extend(["--branch", ref])
        command.extend([repo_url, str(destination)])

        self._run_command(command, cwd=workspace, timeout=self._settings.repo_scan_clone_timeout_seconds)
        return destination

    def _run_scanner(self, repo_path: Path, scanner: RepoScannerName) -> RepoScannerResult:
        if scanner == RepoScannerName.PROWLER:
            return RepoScannerResult(
                scanner=scanner,
                status=AnalysisStatus.FAILED,
                error_message="Prowler is planned for phase 2 because it requires AWS account posture access, not only repository contents.",
                summary=summarize_findings([]),
            )

        executable = shutil.which(scanner.value)
        if not executable:
            return RepoScannerResult(
                scanner=scanner,
                status=AnalysisStatus.FAILED,
                error_message=f"{scanner.value} is not installed in the scanning environment.",
                summary=summarize_findings([]),
            )

        handlers: Dict[RepoScannerName, Callable[[Path, str], RepoScannerResult]] = {
            RepoScannerName.CHECKOV: self._run_checkov,
            RepoScannerName.TRIVY: self._run_trivy,
            RepoScannerName.GITLEAKS: self._run_gitleaks,
            RepoScannerName.SEMGREP: self._run_semgrep,
            RepoScannerName.TFSEC: self._run_tfsec,
        }

        handler = handlers.get(scanner)
        if handler is None:
            return RepoScannerResult(
                scanner=scanner,
                status=AnalysisStatus.FAILED,
                error_message=f"Scanner {scanner.value} is not supported yet.",
                summary=summarize_findings([]),
            )

        return handler(repo_path, executable)

    def _run_checkov(self, repo_path: Path, executable: str) -> RepoScannerResult:
        command = [executable, "-d", str(repo_path), "-o", "json"]
        return self._run_json_scanner(
            scanner=RepoScannerName.CHECKOV,
            command=command,
            parser=lambda payload: self._parse_checkov(payload),
            cwd=repo_path,
        )

    def _run_trivy(self, repo_path: Path, executable: str) -> RepoScannerResult:
        command = [executable, "fs", "--format", "json", str(repo_path)]
        return self._run_json_scanner(
            scanner=RepoScannerName.TRIVY,
            command=command,
            parser=lambda payload: self._parse_trivy(payload),
            cwd=repo_path,
        )

    def _run_semgrep(self, repo_path: Path, executable: str) -> RepoScannerResult:
        command = [executable, "scan", "--config", "auto", "--json", str(repo_path)]
        return self._run_json_scanner(
            scanner=RepoScannerName.SEMGREP,
            command=command,
            parser=lambda payload: self._parse_semgrep(payload),
            cwd=repo_path,
        )

    def _run_tfsec(self, repo_path: Path, executable: str) -> RepoScannerResult:
        command = [executable, str(repo_path), "--format", "json"]
        return self._run_json_scanner(
            scanner=RepoScannerName.TFSEC,
            command=command,
            parser=lambda payload: self._parse_tfsec(payload),
            cwd=repo_path,
        )

    def _run_gitleaks(self, repo_path: Path, executable: str) -> RepoScannerResult:
        report_path = repo_path / ".gitleaks-report.json"
        command = [
            executable,
            "detect",
            "--source",
            str(repo_path),
            "--report-format",
            "json",
            "--report-path",
            str(report_path),
            "--no-banner",
        ]
        started_at = time.perf_counter()
        try:
            self._run_command(command, cwd=repo_path, timeout=self._settings.repo_scan_scanner_timeout_seconds, allow_non_zero=True)
            payload = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else []
            findings = self._parse_gitleaks(payload)
            return RepoScannerResult(
                scanner=RepoScannerName.GITLEAKS,
                status=AnalysisStatus.COMPLETED,
                findings=findings,
                summary=summarize_findings(findings),
                command=command,
                duration_ms=int((time.perf_counter() - started_at) * 1000),
            )
        except Exception as exc:
            return RepoScannerResult(
                scanner=RepoScannerName.GITLEAKS,
                status=AnalysisStatus.FAILED,
                error_message=str(exc),
                command=command,
                duration_ms=int((time.perf_counter() - started_at) * 1000),
                summary=summarize_findings([]),
            )
        finally:
            report_path.unlink(missing_ok=True)

    def _run_json_scanner(
        self,
        scanner: RepoScannerName,
        command: List[str],
        parser: Callable[[Any], List[Finding]],
        cwd: Path,
    ) -> RepoScannerResult:
        started_at = time.perf_counter()
        try:
            completed = self._run_command(command, cwd=cwd, timeout=self._settings.repo_scan_scanner_timeout_seconds, allow_non_zero=True)
            payload = json.loads(completed.stdout or "{}")
            findings = parser(payload)
            return RepoScannerResult(
                scanner=scanner,
                status=AnalysisStatus.COMPLETED,
                findings=findings,
                summary=summarize_findings(findings),
                command=command,
                duration_ms=int((time.perf_counter() - started_at) * 1000),
            )
        except Exception as exc:
            return RepoScannerResult(
                scanner=scanner,
                status=AnalysisStatus.FAILED,
                error_message=str(exc),
                command=command,
                duration_ms=int((time.perf_counter() - started_at) * 1000),
                summary=summarize_findings([]),
            )

    def _run_command(
        self,
        command: List[str],
        cwd: Path,
        timeout: int,
        allow_non_zero: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            shell=False,
        )
        if completed.returncode != 0 and not allow_non_zero:
            stderr = completed.stderr.strip() or completed.stdout.strip() or "Command failed"
            raise RuntimeError(stderr)
        return completed

    def _parse_checkov(self, payload: Dict[str, Any]) -> List[Finding]:
        findings: List[Finding] = []
        for entry in payload.get("results", {}).get("failed_checks", []):
            findings.append(
                self._build_finding(
                    source="checkov",
                    rule_id=entry.get("check_id", "CHECKOV"),
                    title=entry.get("check_name", "Checkov finding"),
                    description=entry.get("description", "Checkov reported an issue."),
                    severity=self._severity_from_text(entry.get("severity")),
                    recommendation=entry.get("guideline") or "Review the failed Checkov control and remediate the infrastructure configuration.",
                    resource=entry.get("resource"),
                    line_number=self._line_number(entry.get("file_line_range")),
                    references=[entry.get("guideline")] if entry.get("guideline") else [],
                    metadata={"file_path": entry.get("file_path"), "scanner": "checkov"},
                )
            )
        return findings

    def _parse_trivy(self, payload: Dict[str, Any]) -> List[Finding]:
        findings: List[Finding] = []
        for result in payload.get("Results", []):
            target = result.get("Target")
            for vulnerability in result.get("Vulnerabilities", []) or []:
                references = vulnerability.get("PrimaryURL")
                findings.append(
                    self._build_finding(
                        source="trivy",
                        rule_id=vulnerability.get("VulnerabilityID", "TRIVY"),
                        title=vulnerability.get("Title") or vulnerability.get("PkgName") or "Trivy finding",
                        description=vulnerability.get("Description") or "Trivy identified a vulnerability in repository contents.",
                        severity=self._severity_from_text(vulnerability.get("Severity")),
                        recommendation=vulnerability.get("FixedVersion") and f"Upgrade to fixed version {vulnerability.get('FixedVersion')}." or "Review the vulnerable package or file and update it to a non-vulnerable version.",
                        resource=target,
                        references=[references] if references else [],
                        metadata={"pkg_name": vulnerability.get("PkgName"), "installed_version": vulnerability.get("InstalledVersion"), "scanner": "trivy"},
                    )
                )
        return findings

    def _parse_gitleaks(self, payload: List[Dict[str, Any]]) -> List[Finding]:
        findings: List[Finding] = []
        for entry in payload:
            findings.append(
                self._build_finding(
                    source="gitleaks",
                    rule_id=entry.get("RuleID", "GITLEAKS"),
                    title=entry.get("Description") or "Potential secret detected",
                    description=entry.get("Description") or "Gitleaks detected a potential secret in the repository.",
                    severity=Severity.CRITICAL,
                    recommendation="Rotate the exposed secret, remove it from source control, and add secret scanning prevention.",
                    resource=entry.get("File"),
                    line_number=entry.get("StartLine"),
                    references=[],
                    metadata={"commit": entry.get("Commit"), "author": entry.get("Author"), "scanner": "gitleaks"},
                )
            )
        return findings

    def _parse_semgrep(self, payload: Dict[str, Any]) -> List[Finding]:
        findings: List[Finding] = []
        for result in payload.get("results", []):
            extra = result.get("extra", {})
            metadata = extra.get("metadata", {}) if isinstance(extra, dict) else {}
            references = metadata.get("references") if isinstance(metadata, dict) else []
            findings.append(
                self._build_finding(
                    source="semgrep",
                    rule_id=result.get("check_id", "SEMGREP"),
                    title=extra.get("message") or result.get("check_id", "Semgrep finding"),
                    description=extra.get("message") or "Semgrep identified a possible security issue.",
                    severity=self._severity_from_text((metadata or {}).get("severity") or extra.get("severity")),
                    recommendation=(metadata or {}).get("fix") or "Review the affected code path and apply the Semgrep remediation guidance.",
                    resource=result.get("path"),
                    line_number=((result.get("start") or {}).get("line")),
                    references=references if isinstance(references, list) else [],
                    metadata={"scanner": "semgrep", "category": (metadata or {}).get("category")},
                )
            )
        return findings

    def _parse_tfsec(self, payload: Any) -> List[Finding]:
        results = payload.get("results", []) if isinstance(payload, dict) else payload
        findings: List[Finding] = []
        for entry in results or []:
            findings.append(
                self._build_finding(
                    source="tfsec",
                    rule_id=entry.get("rule_id", "TFSEC"),
                    title=entry.get("long_id") or entry.get("description") or "tfsec finding",
                    description=entry.get("description") or "tfsec reported a Terraform issue.",
                    severity=self._severity_from_text(entry.get("severity")),
                    recommendation=entry.get("resolution") or "Review the Terraform rule failure and apply the recommended control.",
                    resource=entry.get("resource"),
                    line_number=entry.get("location", {}).get("start_line") if isinstance(entry.get("location"), dict) else None,
                    references=entry.get("links") or [],
                    metadata={"scanner": "tfsec", "location": entry.get("location")},
                )
            )
        return findings

    def _build_finding(
        self,
        source: str,
        rule_id: str,
        title: str,
        description: str,
        severity: Severity,
        recommendation: str,
        resource: Optional[str],
        line_number: Optional[int],
        references: List[str],
        metadata: Dict[str, Any],
    ) -> Finding:
        return Finding(
            id=f"{source}:{rule_id}:{resource or title}",
            rule_id=rule_id,
            title=title,
            category=FindingCategory.SECURITY,
            description=description,
            severity=severity,
            resource=resource,
            line_number=line_number,
            recommendation=recommendation,
            references=[reference for reference in references if reference],
            metadata=metadata,
        )

    def _severity_from_text(self, value: Any) -> Severity:
        normalized = str(value or "").strip().lower()
        mapping = {
            "critical": Severity.CRITICAL,
            "high": Severity.HIGH,
            "medium": Severity.MEDIUM,
            "moderate": Severity.MEDIUM,
            "low": Severity.LOW,
            "info": Severity.INFO,
            "informational": Severity.INFO,
            "warning": Severity.MEDIUM,
            "error": Severity.HIGH,
        }
        return mapping.get(normalized, Severity.MEDIUM)

    def _line_number(self, value: Any) -> Optional[int]:
        if isinstance(value, list) and value:
            first = value[0]
            return first if isinstance(first, int) else None
        if isinstance(value, int):
            return value
        return None


def get_repo_scan_service() -> RepoScanService:
    return RepoScanService(get_settings())
