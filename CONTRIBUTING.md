# Contributing to InfraMind AI

Thank you for your interest in contributing! Please read this guide before opening a PR.

---

## Prerequisites

| Tool | Version |
|---|---|
| Node.js | ≥ 20 |
| pnpm | ≥ 9 |
| Docker | ≥ 24 |

Install pnpm if you haven't already:

```bash
corepack enable
corepack prepare pnpm@9.1.0 --activate
```

---

## Local setup

```bash
# 1. Clone the repo
git clone https://github.com/JeevaByte/inframind-ai.git
cd inframind-ai

# 2. Install dependencies
pnpm install

# 3. Copy and fill environment variables
cp .env.example .env
# Edit .env with your values

# 4. Start infrastructure (Postgres + Redis)
docker compose up postgres redis -d

# 5. Start all apps in dev mode
pnpm dev
```

Apps:

| App | URL |
|---|---|
| Web | http://localhost:3000 |
| API | http://localhost:3001 |
| API docs | http://localhost:3001/documentation |

---

## Development workflow

1. **Create a branch** — `git checkout -b feat/my-feature`
2. **Make changes** — follow [Coding Standards](docs/CODING_STANDARDS.md)
3. **Test** — `pnpm test`
4. **Lint** — `pnpm lint && pnpm typecheck`
5. **Commit** — use [Conventional Commits](https://www.conventionalcommits.org/)
6. **Open a PR** — fill in the PR template

---

## Scripts reference

| Command | Description |
|---|---|
| `pnpm dev` | Start all apps in watch mode |
| `pnpm build` | Build all packages and apps |
| `pnpm test` | Run all tests |
| `pnpm lint` | Lint all TypeScript files |
| `pnpm typecheck` | Type-check all packages |
| `pnpm format` | Format all files with Prettier |
| `pnpm clean` | Remove all build artefacts |

---

## Questions?

Open a [GitHub Discussion](https://github.com/JeevaByte/inframind-ai/discussions) or file an issue.
