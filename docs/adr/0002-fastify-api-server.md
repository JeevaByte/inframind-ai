# ADR-0002: Fastify for the API Server

**Date:** 2026-05-06  
**Status:** Accepted  
**Deciders:** Platform Architect

## Context

We need an HTTP and WebSocket server for the InfraMind AI backend. Candidates considered: Express, Fastify, Hono, NestJS.

## Decision

Use **Fastify 5**:
- Highest raw throughput among Node.js frameworks (benchmark-proven).
- Schema-first request validation with JSON Schema — maps naturally to Zod.
- Official plugins for CORS, Helmet, JWT, rate limiting, Swagger.
- TypeScript support is first-class.
- Lighter than NestJS; avoids heavy DI framework lock-in.

## Consequences

- Team must learn Fastify's plugin system (`fastify-plugin`, lifecycle hooks).
- If NestJS-style DI is later needed, we can layer in a lightweight container (e.g. `awilix`).
