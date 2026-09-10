# Vexmera launch gap plan

Last reviewed: 2026-09-10

This document tracks the shortest safe path from the current build to a five-company private beta. It intentionally excludes any change to live ad execution, campaign budgets, bids, billing credentials, secrets, permissions, domains, DNS, or customer data.

## Current verified position

- GitHub repository is reachable and writable.
- Latest verified `main` commit: `88e96eefd64ea62e6a9123d88f863c1e53feb78c`.
- GitHub reports Vercel deployment status `success` for that commit.
- Public landing, authenticated app shell, onboarding guards, connector-state UX, owner/admin disconnect controls, privacy controls, accessibility hardening, session-cookie input bounds and customer-safe sync summaries are present.
- Google and Meta read-only connector paths have bounded retry/response-safety hardening. Meta also has bounded Insights pagination.
- Google Analytics sessions are separated from paid-click semantics at the read boundary so website sessions cannot inflate ad CPC/CTR calculations.
- Stripe code, public pricing and operator docs use the canonical Start / Growth / Pro model at 995 / 1,495 / 2,995 SEK monthly. Checkout remains fail-closed until the current test-mode Price catalog and explicit pricing-version marker are verified.
- The historical Starter / Growth / Scale Stripe test catalog is retained only as migration evidence and must not be used for current Checkout.
- Google Ads manager-to-client relationship is accepted and active. Google Ads Basic Access approval still requires external verification.
- Direct ChatGPT -> Vercel project/log inspection remains blocked because the connected Vercel account currently returns no teams, even though GitHub -> Vercel deployment status works.

## Priority 0: restore reliable production observability

Goal: make production state directly inspectable before external users are invited.

Remaining gates:

- restore direct Vercel connector visibility to the existing project without changing DNS, domains, secrets or production permissions;
- inspect current production runtime errors/logs;
- re-run `/health/runtime` and `/health/beta-readiness` evidence after final environment reconciliation;
- complete authenticated real-browser QA for `/app`, sign-in, onboarding, connector states and destructive privacy controls.

## Priority 1: finish real connector verification

Goal: prove the product works with real read-only marketing data.

Completed foundations:

- Google/Meta zero-data and provider-error states are distinct in the customer UI;
- connector secrets are excluded from normal API responses;
- Google read requests have bounded transient retry and payload validation;
- Meta Insights has bounded retry, pagination and loop/limit protection;
- disconnect is available to owner/admin with explicit confirmation;
- all external ad execution remains locked off.

Remaining gates:

- verify Google Ads Basic Access approval;
- verify `GOOGLE_ADS_LOGIN_CUSTOMER_ID` if required by the active manager hierarchy;
- run one controlled real Google Ads read-only sync after approval;
- run one controlled live Meta read-only sync with campaign data where available;
- capture only sanitized provider diagnostics if either source fails.

## Priority 2: reconcile the current Stripe sandbox

Goal: prove the commercial flow without touching live-mode billing.

Completed foundations:

- Start / Growth / Pro is the canonical code and customer-facing plan model;
- current expected monthly amounts are 995 / 1,495 / 2,995 SEK;
- Checkout is blocked until the exact current pricing version is approved;
- the canonical verifier rejects live-mode, inactive, wrong-currency, wrong-interval and wrong-amount Price objects;
- verifier output excludes Stripe secrets, configured Price IDs and raw Stripe errors.

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
- perform final performance pass on landing and authenticated shell;
- fix only evidence-backed defects found in that pass.

## Working completion estimate

These percentages are planning estimates, not release certification.

- Public website / conversion layer: 92%
- Core application UI and navigation: 90%
- Backend / diagnostics / safety foundations: 95%
- Google + Meta production-read integration readiness: 82%
- Billing sandbox readiness: 80%
- Five-company pilot operations / documentation: 92%
- Production observability and final deployed QA: 65%
- Overall private-beta readiness: approximately 88%

The remaining work is now concentrated in external verification and final evidence rather than missing core product code. The largest gates are direct production observability, Google Ads Basic Access plus a real Ads sync, current Stripe sandbox reconciliation and E2E billing verification, authenticated browser QA, and final legal sign-off.

## Immediate next action

1. Restore direct Vercel read-only visibility without changing production settings.
2. Verify current runtime/readiness evidence and authenticated browser behavior.
3. Verify Google Ads Basic Access and run the first real post-link read-only Ads sync.
4. Reconcile the Start/Growth/Pro Stripe sandbox and run the canonical verifier.
5. Complete Stripe sandbox Checkout/webhook/Portal E2E.
6. Finalize legal details and run the five-company pilot only after the above gates are clear.
