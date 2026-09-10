# Vexmera launch gap plan

Last reviewed: 2026-09-10

This document tracks the shortest safe path from the current build to a five-company private beta. It intentionally excludes changes to live ad execution, campaign budgets, bids, live billing, secrets, permissions, domains, DNS or customer data.

## How to read this file

Do not use a hard-coded commit SHA in this document as a release pointer. Before every autonomous build or launch check, verify the current `main` SHA, open pull requests, GitHub Actions status and deployment status directly in GitHub. This prevents a stale document from being treated as current production truth.

## Current verified position

- GitHub repository access is working and the latest checked `main` GitHub Actions run was successful.
- At this review, Vercel reported `Deployment rate limited — retry in 24 hours.` That is a deployment-capacity status, not evidence of a code-test failure. Production deployment of newer commits therefore remains unverified until Vercel accepts another build.
- Public landing, authenticated app shell, onboarding guards, connector-state UX, owner/admin disconnect controls, privacy controls, accessibility hardening, session-cookie input bounds and customer-safe sync summaries are present.
- Public `/health/runtime` is intentionally minimal in production and no longer exposes provider, database, Stripe, SMTP, OAuth or secret-configuration booleans.
- Public beta-readiness output is limited to the small safety surface needed to prove the private-beta execution posture. Full configuration checks belong in operator preflight.
- Google and Meta read-only connector paths have bounded retry and malformed-response hardening. Meta also has bounded Insights pagination, loop/page-limit protection and campaign/date deduplication.
- Google Analytics sessions are separated from paid-click semantics so website sessions cannot inflate paid CPC/CTR calculations.
- Google Ads manager-to-client relationship is accepted and active. Google Ads Basic Access approval still requires external verification.
- Stripe code and customer-facing pricing use Start / Growth / Pro at 995 / 1,495 / 2,995 SEK monthly. Checkout remains fail-closed until the current test-mode catalog and explicit pricing-version marker are verified.
- Production environment guards no longer synthesize historical `STRIPE_PRICE_STARTER` or `STRIPE_PRICE_SCALE` aliases from the current pricing model.
- Flexible persisted approval/job/Core-action payloads are bounded to 64 KiB of compact UTF-8 JSON before persistence.
- Direct ChatGPT to Vercel project/log inspection remains blocked while the connected Vercel account exposes no usable team/project context.

## Priority 0: restore reliable production observability

Goal: prove what is actually deployed before inviting external users.

Remaining gates:

- wait for or resolve the Vercel deployment rate limit without changing DNS, domains, secrets or production permissions;
- verify the accepted production deployment revision through minimal `/health/runtime` output;
- run operator `scripts/preflight.py` in the configured environment rather than relying on public configuration booleans;
- inspect production errors/logs once direct Vercel visibility is available;
- complete authenticated real-browser QA for `/app`, sign-in, onboarding, connector states and destructive privacy controls.

## Priority 1: finish real connector verification

Goal: prove the product works with real read-only marketing data.

Completed foundations:

- Google/Meta zero-data and provider-error states are distinct in the customer UI;
- connector secrets are excluded from normal API responses;
- Google read requests have bounded transient retry and payload validation;
- Meta Insights has bounded retry, pagination and loop/page-limit protection;
- malformed provider responses fail safely instead of becoming false empty-account states;
- disconnect is available to owner/admin with explicit confirmation;
- all external ad execution remains locked off.

Remaining gates:

- verify Google Ads Basic Access approval;
- verify `GOOGLE_ADS_LOGIN_CUSTOMER_ID` if required by the active manager hierarchy;
- run one controlled real Google Ads read-only sync after approval;
- run one controlled real Meta read-only sync with campaign data where available;
- verify long-lived Meta token lifecycle/expiry behavior with a real account;
- capture only sanitized provider diagnostics if either source fails.

## Priority 2: reconcile the current Stripe sandbox

Goal: prove the commercial flow without touching live-mode billing.

Completed foundations:

- Start / Growth / Pro is the canonical code and customer-facing plan model;
- current expected monthly amounts are 995 / 1,495 / 2,995 SEK;
- Checkout is blocked until the exact current pricing version is approved;
- the canonical verifier rejects live-mode, inactive, wrong-currency, wrong-interval and wrong-amount Price objects;
- verifier output excludes Stripe secrets, configured Price IDs and raw Stripe errors;
- production guards no longer recreate historical Starter/Scale environment aliases.

Remaining gates:

- create or independently verify the three current test-mode Stripe Prices;
- point the Vercel test/sandbox environment at those Price IDs;
- confirm `STRIPE_SECRET_KEY` belongs to the same Stripe test account;
- run `python scripts/verify_stripe_catalog.py` in the configured environment and require `catalog_ok=true`;
- set `VEZMORA_STRIPE_PRICING_VERSION=2026-09-start-growth-pro` only after that verification passes;
- verify signed sandbox webhook, Checkout/trial and Customer Portal end-to-end;
- make a separate VAT/tax decision before any live-mode paid launch.

## Priority 3: legal and pilot operations

Goal: make the private beta supportable and safe.

Completed foundations:

- public Privacy Policy and Terms routes exist and are linked;
- connector disconnect, synchronized-history deletion, account deletion and analytics-consent controls are implemented;
- pilot runbook, go/no-go checks and secrets-safe evidence template exist;
- private-beta execution locks are fail-closed.

Remaining gates:

- finalize legal entity/contact details;
- finalize concrete retention periods and subprocessors;
- complete legal review of Privacy Policy and Beta Terms;
- use the evidence template for each pilot company;
- enforce stop conditions for cross-tenant data, unexpected write access, billing anomalies or privacy failures.

## Priority 4: final product verification

Only after the gates above are materially clear:

- complete authenticated browser QA on desktop and mobile;
- verify loading/empty/error states with real connected accounts;
- verify first-use guidance with a fresh business account;
- perform a final evidence-driven performance pass on landing and authenticated shell;
- fix only defects supported by reproducible evidence.

## Working completion estimate

These percentages are planning estimates, not release certification.

- Public website / conversion layer: 92%
- Core application UI and navigation: 90%
- Backend / diagnostics / safety foundations: 96%
- Google + Meta production-read integration readiness: 84%
- Billing sandbox readiness: 82%
- Five-company pilot operations / documentation: 93%
- Production observability and final deployed QA: 65%
- Overall private-beta readiness: approximately 89%

The remaining work is concentrated in external verification and deployed evidence rather than missing core product code. The largest gates are Vercel deployment/observability, Google Ads Basic Access plus a real read-only sync, current Stripe sandbox reconciliation and E2E billing verification, authenticated browser QA, real Meta lifecycle verification and final legal sign-off.

## Immediate next action

1. Recheck GitHub `main`, CI and Vercel status at execution time.
2. Once Vercel accepts a build, verify the deployed revision and run operator preflight.
3. Complete authenticated browser QA against that verified deployment.
4. Verify Google Ads Basic Access and run the first controlled read-only Ads sync.
5. Reconcile the Start/Growth/Pro Stripe sandbox and complete signed webhook/Checkout/Portal E2E.
6. Verify a real Meta read-only account including token lifecycle and empty/error behavior.
7. Finalize legal details and run the five-company pilot only after the preceding gates are clear.
