# InfraMind AI — Architecture

## Overview

InfraMind AI is an intelligent infrastructure automation platform that combines LLM-powered agents with real-time cloud resource management. Users interact via a conversational interface; agents plan and execute infrastructure changes safely with human-in-the-loop approval flows.

---

## Monorepo layout

```
inframind-ai/
├── apps/
│   ├── api/          # Fastify REST + WebSocket API server (Node.js)
│   └── web/          # Next.js 14 web application (App Router)
├── packages/
│   ├── shared/       # Shared TypeScript types, interfaces, utilities
│   └── config/       # Zod-validated environment config helpers
├── docs/             # Architecture & coding standards docs
├── .github/          # GitHub Actions workflows, PR templates
├── tsconfig.base.json
├── .eslintrc.cjs
├── .prettierrc
└── pnpm-workspace.yaml
```

---

## Tech stack

| Layer | Technology | Rationale |
|---|---|---|
| Language | TypeScript 5 (strict) | End-to-end type safety |
| Package manager | pnpm 9 + workspaces | Fast, disk-efficient monorepo |
| API server | Fastify 4 | High throughput, schema-first |
| Web frontend | Next.js 14 (App Router) | SSR, RSC, file-based routing |
| Validation | Zod | Runtime schema validation across layers |
| Auth | JWT (via @fastify/jwt) | Stateless, easy horizontal scale |
| AI integration | OpenAI / Anthropic (pluggable via `AIProvider` interface) | Swap models without touching business logic |
| Database | PostgreSQL (via Prisma ORM) | Relational, ACID, great TypeScript support |
| Cache / queue | Redis | Session cache, job queue, pub-sub |
| Containerisation | Docker + Docker Compose | Consistent local and CI environments |
| CI/CD | GitHub Actions | Native, fast, free for OSS |
| Testing | Vitest | Fast, ESM-native, Jest-compatible API |

---

## Key design principles

### 1. Ports & Adapters (Hexagonal Architecture)
Business logic in `services/` is free of framework concerns. Infrastructure (DB, HTTP, AI providers) is injected via interfaces defined in `@inframind/shared`.

### 2. Shared-nothing data ownership
Each `app` owns its own database schema. Shared data is exchanged via the API or typed events, never direct DB cross-access.

### 3. Schema-first API
All request/response shapes are defined with Zod schemas and auto-generated as JSON Schema for Swagger. The frontend consumes the same types via `@inframind/shared`.

### 4. Human-in-the-loop by default
Destructive infrastructure actions require explicit user approval before execution. The agent surfaces a structured plan that the user must confirm.

### 5. Observability
Structured JSON logging (Pino), OpenTelemetry traces, and health-check endpoints are built in from day one.

---

## Data flow

```
User (Browser)
    │  HTTPS / WebSocket
    ▼
apps/web (Next.js)          ─── Server Actions / API routes ──▶  apps/api (Fastify)
                                                                        │
                                                            ┌───────────┼───────────┐
                                                            ▼           ▼           ▼
                                                       PostgreSQL    Redis     AI Provider
                                                       (Prisma)   (BullMQ)  (OpenAI/Anthropic)
```

---

## Security considerations

- All secrets loaded via environment variables, validated with Zod at startup.
- JWT tokens are short-lived (15 min access / 7 day refresh).
- Rate limiting on all public API endpoints.
- Helmet sets secure HTTP headers.
- Database queries use parameterised statements (Prisma default).
- No secrets committed to repository — `.env` is git-ignored.

---

## Deployment targets

| Environment | Infrastructure |
|---|---|
| Local dev | Docker Compose |
| Staging | Railway / Render |
| Production | AWS ECS (Fargate) + RDS + ElastiCache |

---

## ADRs (Architecture Decision Records)

ADRs live in `docs/adr/`. Use the template `docs/adr/TEMPLATE.md`.
