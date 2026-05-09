# Buyer Objections Action Plan

> **Status update (2026-05-08):** This project has been renamed **infralint** and
> released under Apache 2.0. See the root [README](../../README.md) and
> [CHANGELOG](../../CHANGELOG.md). The strategic analysis below remains valid;
> product/positioning decisions are now reflected in the current codebase.

## Purpose

This document captures common objections raised by enterprise buyers and
defines concrete actions to address each one.

## Objections and Responses

### "We already use Checkov / TFLint."

**Action:** Publish a side-by-side comparison showing AI-powered suggestions and
reduced time-to-remediation. Offer a migration guide.

### "Open source means no support."

**Action:** Define and publish enterprise support tiers with SLA commitments.
Highlight community health metrics (response time, issue closure rate).

### "We can't send our IaC to an external AI service."

**Action:** Document the local/self-hosted LLM option. Clarify that scanning
runs entirely locally by default; AI features are opt-in.

### "The rule set is too small."

**Action:** Publish a rule coverage dashboard. Prioritise expanding high-demand
providers (AWS, Azure, GCP) in Q3.

### "We need SOC 2 / ISO 27001 compliance."

**Action:** Begin SOC 2 Type I audit process. Publish a shared responsibility
model for self-hosted deployments.

## Tracking

Each action item above should be linked to a GitHub issue and assigned an owner
before the next GTM review.
