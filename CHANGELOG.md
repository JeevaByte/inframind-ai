# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-05-08

### Added

- AI/Prompt Engineer layer: Pydantic domain models (`InfraResource`, `Finding`, `RiskScore`, `Recommendation`, `AnalysisResult`), prompt template engine with variable substitution and conditional blocks, 8 resource-type-specific analysis prompt templates, risk scorer, response formatter, recommendation engine, and AI orchestration service
- FastAPI backend with file upload endpoints (`/api/v1/files/upload/bulk`) and bulk analysis endpoints (`/api/v1/analysis/bulk`, `/api/v1/analysis/{id}`)
- Next.js 15 frontend (`apps/web`) with Tailwind CSS, shadcn/ui components, landing page, dashboard, file upload flow, and results pages
- Next.js API proxy routes (`/api/analysis` POST and `/api/analysis/[id]` GET) so the browser never calls FastAPI directly; `FASTAPI_URL` remains server-side only
- Terraform infrastructure modules on AWS: IAM (Lambda execution role + least-privilege S3-read policy), S3 (versioned, AES-256-encrypted artifacts + lifecycle-managed logs buckets), Lambda (function + CloudWatch log group + X-Ray active tracing + error-rate alarm), API Gateway v2 (HTTP API with `ANY /{proxy+}` → Lambda integration, per-environment CORS)
- GitHub Actions CI/CD pipelines for frontend, backend, infrastructure, and security scanning; Vercel frontend deployment; Lambda backend deployment; per-environment configuration

### Changed

- Collapsed dual-backend architecture (Fastify `apps/api/` + FastAPI `backend/`) to a single FastAPI backend; `docker-compose.yml` updated to build from `./backend` on port 8000 with `web` depending on `backend`
- Consolidated duplicate AI module: removed top-level `ai/` draft in favour of `backend/app/services/ai/` as the sole authoritative AI module

### Removed

- Removed `apps/api/` Fastify skeleton (zero business logic; FastAPI owns the entire AI pipeline)
- Removed top-level `ai/` directory (unreferenced earlier draft superseded by `backend/app/services/ai/`)

### Security

- Bumped `python-multipart` from 0.0.9 to 0.0.22, patching arbitrary file-write (multipart filename traversal) and DoS via malformed boundary
- Upgraded Next.js from 14.2.35 to 15.5.15, patching Server Components HTTP request deserialisation DoS
- Upgraded Fastify from ^4.27.0 to ^5.8.5, patching Content-Type header tab-character and leading-space body-schema validation bypass CVEs; all `@fastify/*` plugins bumped to Fastify-5-compatible majors

[Unreleased]: https://github.com/JeevaByte/inframind-ai/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/JeevaByte/inframind-ai/releases/tag/v0.1.0
