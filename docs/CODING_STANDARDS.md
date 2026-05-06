# InfraMind AI — Coding Standards

These standards apply to all TypeScript code in this monorepo. They are enforced automatically by ESLint, Prettier, and TypeScript strict mode.

---

## TypeScript

- **Strict mode is non-negotiable.** All `tsconfig.json` files extend `tsconfig.base.json` which enables `strict: true`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, and more.
- Prefer `type` imports: `import type { Foo } from "..."`.
- Never use `any`. Use `unknown` and narrow with type guards.
- Never use non-null assertions (`!`). Prove nullability instead.
- Prefer `interface` for public API shapes and `type` for unions/intersections/aliases.
- Use `const` assertions for literal arrays/objects that act as enums.

---

## File & folder naming

| Artefact | Convention | Example |
|---|---|---|
| Source files | `kebab-case.ts` | `agent-session.ts` |
| React components | `PascalCase.tsx` | `AgentChat.tsx` |
| Test files | `*.test.ts` / `*.spec.ts` | `slugify.test.ts` |
| Directories | `kebab-case` | `agent-sessions/` |

---

## Imports

1. Standard library / Node built-ins
2. External packages
3. Workspace packages (`@inframind/*`)
4. Internal modules (absolute `@/`)
5. Relative imports

Groups are separated by blank lines (enforced by `eslint-plugin-import`).

---

## Functions & variables

- Prefer named function declarations for top-level functions.
- Use arrow functions for callbacks and inline expressions.
- Prefer `const` everywhere; use `let` only when reassignment is needed.
- Name booleans with `is`, `has`, `can`, `should` prefix: `isLoading`, `hasError`.
- Avoid magic numbers — use named constants from `@inframind/shared/constants`.

---

## Error handling

- Never swallow errors silently. Always log or re-throw.
- Use the `ApiError` / `ApiResponse` types from `@inframind/shared` for all API boundaries.
- Prefer early returns over deeply nested conditionals.
- Async functions must either return a promise that propagates errors or catch and handle them explicitly.

---

## Testing

- Co-locate unit tests with source: `src/utils/slugify.ts` → `src/utils/slugify.test.ts`.
- Integration tests live in `src/__tests__/`.
- Aim for high coverage of business logic (services, utils). Infrastructure adapters are tested via integration tests.
- Test naming: `describe("slugify")` → `it("returns empty string for empty input")`.
- No `test.only` or `describe.only` committed to the repository.

---

## Git & pull requests

- Branch naming: `feat/<short-description>`, `fix/<short-description>`, `chore/<short-description>`.
- Commit messages: [Conventional Commits](https://www.conventionalcommits.org/) — `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`.
- Every PR must pass lint, typecheck, and tests before merge.
- PRs should be small and focused. Large changes should be broken into a stack.

---

## Comments & documentation

- Write self-documenting code; only add comments when the *why* is non-obvious.
- Use JSDoc (`/** */`) for all exported functions, types, and interfaces in `packages/`.
- Keep `docs/` up to date when making architectural changes.

---

## Security

- Never log secrets, tokens, or PII.
- All environment variables are loaded and validated at startup via `@inframind/config`.
- Validate all user input with Zod before processing.
- Use parameterised queries — never concatenate user input into SQL or shell commands.
