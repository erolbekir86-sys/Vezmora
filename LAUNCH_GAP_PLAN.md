# Vexmera launch gap plan

Last reviewed: 2026-09-07

This document tracks the shortest safe path from the current build to a five-company private beta. It intentionally excludes any change to live ad execution, campaign budgets, bids, billing credentials, secrets, permissions, domains, DNS, or customer data.

## Current verified position

- GitHub repository is reachable and writable.
- Latest observed main commit: `ba58105ad5cdd7edf3bc1362d0ec53a76cc956e4` (`Load conversion-focused landing enhancements`).
- GitHub reports the Vercel deployment status for that commit as `success`.
- Public landing work now includes conversion-focused enhancements, premium/mobile styling, founder/brand refinements and fail-open rendering protection against blank-page reveal failures.
- App UI modernization, auth contrast work, frontend smoke tests, JavaScript syntax checks, connector empty-state hardening, database diagnostics, beta-readiness diagnostics and pilot safety guardrails are already present.
- Direct ChatGPT -> Vercel project inspection remains blocked by connector authorization/scope even though GitHub -> Vercel deployment succeeds.

## Priority 0: restore reliable production observability

Goal: make production state directly inspectable before external users are invited.

Success criteria:

- direct Vercel connector can see the existing `vezmora` team/project;
- production runtime errors can be read;
- active deployment revision matches GitHub `main`;
- `/health/runtime` and `/health/beta-readiness` can be checked without exposing secrets;
- public `/` and authenticated `/app` both pass real-browser QA.

Do not change project permissions, DNS, domains or production secrets while solving this. Re-authenticate only the connector scope needed for inspection.

## Priority 1: finish the five-company onboarding path

Goal: a first-time customer can reach useful read-only data without assistance.

Success criteria:

- sign-in and onboarding are understandable on desktop and mobile;
- Google/Meta connection states clearly distinguish: not connected, connecting, connected-empty, connected-with-data and provider/API error;
- disconnect is visible and safe;
- demo data is never presented as live customer data;
- empty states always contain one clear next action;
- all external advertising behavior remains recommendation-only.

## Priority 2: verify real connector reads

Goal: prove the product works with real read-only marketing data.

Success criteria:

- Google Ads Basic Access approved before normal production-client reads;
- one controlled real Google Ads read-only sync succeeds;
- one controlled Meta read-only sync succeeds;
- legitimate zero-data accounts and API/provider failures render different states;
- no campaign, ad, budget or bid mutation path is enabled.

## Priority 3: billing sandbox reconciliation

Goal: prove the commercial flow without touching live payment settings.

Success criteria:

- Stripe test catalog matches the product plan model;
- signed sandbox webhook flow works;
- Checkout/trial flow completes in test mode;
- Customer Portal returns correctly;
- no production billing keys or prices are changed as part of verification.

## Priority 4: legal and pilot operations

Goal: make the private beta supportable and safe.

Success criteria:

- Privacy Policy finalized with concrete entity/contact details, retention periods and subprocessors;
- Beta Terms finalized;
- five-company pilot runbook used for every company;
- evidence template completed without storing tokens, secrets or customer-sensitive raw data;
- stop conditions are enforced for cross-tenant data, unexpected write access, billing anomalies or privacy failures.

## Priority 5: product polish after functional verification

Only after priorities 0-4 pass:

- finish app visual consistency across every route;
- improve loading/skeleton states;
- improve mobile density and touch targets;
- refine KPI visualization and charts;
- add concise first-use guidance where users hesitate;
- run accessibility and keyboard-navigation pass;
- run performance pass on landing and app shell.

## Working completion estimate

These percentages are planning estimates, not release certification.

- Public website / conversion layer: 90%
- Core application UI and navigation: 82%
- Backend / diagnostics / safety foundations: 88%
- Google + Meta production-read integration readiness: 65%
- Billing sandbox readiness: 70%
- Five-company pilot operations / documentation: 85%
- Production observability and final deployed QA: 55%
- Overall private-beta readiness: approximately 78%

The remaining work is disproportionately important: production observability, real read-only connector verification, final browser QA, Stripe sandbox E2E and legal sign-off are the launch gates. Reaching 90% overall should come from closing these gates rather than adding more visual features.

## Immediate next action

1. Restore direct Vercel connector visibility without changing production settings.
2. Inspect production runtime errors and health diagnostics.
3. Run a real-browser smoke pass for `/`, `/app`, login, onboarding and connector states.
4. Fix only evidence-backed defects found in that pass.
5. Then complete one controlled Google/Meta read-only pilot sync and Stripe sandbox E2E.
