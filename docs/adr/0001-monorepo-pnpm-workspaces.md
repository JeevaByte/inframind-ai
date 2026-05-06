# ADR-0001: Monorepo with pnpm Workspaces

**Date:** 2026-05-06  
**Status:** Accepted  
**Deciders:** Platform Architect

## Context

InfraMind AI consists of multiple deployable artefacts (API server, web app) that share types, utilities, and configuration. Without a monorepo we'd need to publish and version these shared packages externally, adding overhead and potential version drift.

## Decision

Use a **pnpm workspace** monorepo. `pnpm` was chosen over `npm` workspaces and `yarn` because:
- Fast installs with hard-linked node_modules (disk-efficient).
- First-class workspace protocol (`workspace:*`) prevents accidental external package resolution.
- Compatible with Turborepo for later incremental build caching if needed.

## Consequences

- Developers must use `pnpm` (version locked via `packageManager` in root `package.json`).
- All internal packages referenced as `workspace:*` — no external registry publishing required during development.
- Adding Turborepo later is straightforward (drop in `turbo.json`).
