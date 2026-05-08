# InfraMind AI

> Intelligent infrastructure automation powered by LLM agents.

[![CI](https://github.com/JeevaByte/inframind-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/JeevaByte/inframind-ai/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![pnpm](https://img.shields.io/badge/maintained%20with-pnpm-cc00ff.svg)](https://pnpm.io/)

---

## What is InfraMind AI?

InfraMind AI is an AI-powered infrastructure review platform for Terraform, Kubernetes, CloudFormation, Dockerfiles, and GitHub Actions. It lets engineers upload infrastructure code, runs structured AI analysis, and returns security, reliability, cost, and best-practice findings with deployment-readiness guidance.

---

## Repository structure

```
inframind-ai/
├── apps/
│   └── web/          # Next.js 15 web application (App Router)
├── backend/          # FastAPI AI analysis backend (Python 3.12)
├── packages/
│   ├── shared/       # Shared TypeScript types, interfaces & utilities
│   └── config/       # Zod-validated environment configuration helpers
├── docs/
│   ├── ARCHITECTURE.md
│   ├── CODING_STANDARDS.md
│   └── adr/          # Architecture Decision Records
├── .github/
│   ├── workflows/ci.yml
│   └── pull_request_template.md
├── docker-compose.yml
├── .env.example
├── tsconfig.base.json
├── .eslintrc.cjs
└── .prettierrc
```

---

## Tech stack

| Layer | Technology |
|---|---|
| Language | TypeScript 5 (strict) / Python 3.12 |
| Package manager | pnpm 9 workspaces |
| AI analysis backend | FastAPI + OpenAI |
| Web frontend | Next.js 15 (App Router) |
| Validation | Zod |
| Testing | Vitest / pytest |
| Containerisation | Docker + Docker Compose |
| CI/CD | GitHub Actions |

---

## Quick start

**Prerequisites:** Node.js ≥ 20, pnpm ≥ 9, Python ≥ 3.11, Docker optional

```bash
# Install Node.js dependencies
pnpm install

# Copy environment templates
cp .env.example .env
cp apps/web/.env.local.example apps/web/.env.local
cp backend/.env.example backend/.env
# → edit the .env files and add OPENAI_API_KEY and other values as needed

# Start the web app
pnpm --filter @inframind/web dev

# Start the FastAPI analysis backend
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

| App | URL |
|---|---|
| Web | http://localhost:3000 |
| AI analysis backend | http://localhost:8000 |
| AI backend docs | http://localhost:8000/docs |

## AI analysis flow

The Phase 2 MVP implements a real AI analysis pipeline:

1. Upload infrastructure files in the web app.
2. The Python backend detects the file type and extracts structured infrastructure context.
3. Parsed context is combined with modular prompts and sent to OpenAI.
4. The backend normalizes the JSON response into findings, scores, deployment readiness, architecture summary, and recommendations.
5. The frontend renders the AI review with severity charts, category tabs, readiness, score breakdowns, and PDF export.

If `OPENAI_API_KEY` is not configured or the model call fails, the backend falls back to a heuristic parser-backed analysis so the demo still works.

## Demo samples

Review-ready infrastructure samples live in [samples](./samples) and include intentionally risky Terraform, Kubernetes, Dockerfile, CloudFormation, and GitHub Actions examples for a stronger AI demo.

---

## Documentation

- [Architecture overview](docs/ARCHITECTURE.md)
- [AI setup guide](docs/AI_SETUP.md)
- [Coding standards](docs/CODING_STANDARDS.md)
- [Contributing guide](CONTRIBUTING.md)
- [ADRs](docs/adr/)

---

## License

MIT © InfraMind AI Contributors