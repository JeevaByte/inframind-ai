# Product Gaps

> **Status update (2026-05-08):** This project has been renamed **infralint** and
> released under Apache 2.0. See the root [README](../../README.md) and
> [CHANGELOG](../../CHANGELOG.md). The strategic analysis below remains valid;
> product/positioning decisions are now reflected in the current codebase.

## Purpose

This document identifies gaps between the current product capabilities and the
requirements expressed by target users and enterprise buyers.

## Gap Analysis

### P0 — Critical

| Gap | Impact | Proposed Solution |
|-----|--------|-------------------|
| No IDE plugin | Reduces developer adoption | VS Code extension (Q3) |
| No SARIF output | Blocks CI integration in some pipelines | Add SARIF formatter |

### P1 — High Priority

| Gap | Impact | Proposed Solution |
|-----|--------|-------------------|
| Limited Terraform provider coverage | Misses cloud-specific rules | Expand provider rule packs |
| No Kubernetes manifest support | Excludes K8s workflows | Add K8s linting module |
| No baseline suppression file | High false-positive noise | Implement `.infralint-baseline` |

### P2 — Medium Priority

| Gap | Impact | Proposed Solution |
|-----|--------|-------------------|
| No web UI | Limits non-CLI users | Optional web dashboard |
| No API server mode | Prevents remote scanning | HTTP API wrapper |

## Prioritisation Notes

P0 gaps should be addressed before the 1.0 GA release. P1 gaps target the 1.x
release cycle. P2 gaps are post-1.0.
