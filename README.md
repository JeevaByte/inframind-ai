# InfraMind AI

> Intelligent infrastructure automation powered by LLM agents.

[![CI](https://github.com/JeevaByte/inframind-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/JeevaByte/inframind-ai/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![pnpm](https://img.shields.io/badge/maintained%20with-pnpm-cc00ff.svg)](https://pnpm.io/)

---

## What is InfraMind AI?

InfraMind AI lets engineers describe infrastructure changes in plain language. An LLM-powered agent interprets the request, plans the required cloud operations, presents a structured approval summary, and — once the engineer confirms — executes the changes safely across AWS, GCP, Azure, and more.

---

## Repository structure

```
inframind-ai/
├── apps/
│   ├── api/          # Fastify 4 REST + WebSocket API (Node.js 20)
│   └── web/          # Next.js 14 web application (App Router)
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
| Language | TypeScript 5 (strict) |
| Package manager | pnpm 9 workspaces |
| API server | Fastify 4 |
| Web frontend | Next.js 14 (App Router) |
| Validation | Zod |
| Testing | Vitest |
| Containerisation | Docker + Docker Compose |
| CI/CD | GitHub Actions |

---

## Quick start

**Prerequisites:** Node.js ≥ 20, pnpm ≥ 9, Docker ≥ 24

```bash
# Install dependencies
pnpm install

# Copy environment template
cp .env.example .env
# → edit .env and add DATABASE_URL, JWT_SECRET, etc.

# Start Postgres + Redis
docker compose up postgres redis -d

# Run all apps in dev mode
pnpm dev
```

| App | URL |
|---|---|
| Web | http://localhost:3000 |
| API | http://localhost:3001 |
| API docs | http://localhost:3001/documentation |

---

## Documentation

- [Architecture overview](docs/ARCHITECTURE.md)
- [Coding standards](docs/CODING_STANDARDS.md)
- [Contributing guide](CONTRIBUTING.md)
- [ADRs](docs/adr/)

---

## License

MIT © InfraMind AI Contributors