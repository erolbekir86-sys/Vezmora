# Vexmera launch gap plan

Last reviewed: 2026-09-14

This document tracks the shortest safe path from the current build to a five-company private beta. It intentionally excludes changes to live ad execution, campaign budgets, bids, live-mode billing, secrets, permissions, domains, DNS or customer data.

## How to read this file

Do not use a hard-coded commit SHA in this document as release truth. Before every launch check, verify the current `main` SHA, open pull requests, GitHub Actions status and the active production deployment. Code/CI evidence, deployed-runtime evidence and authenticated browser evidence are separate gates.

## Current verified position

- The latest verified production baseline before the portal-policy branch is `1b3e5e9722acc44577d1b91a4e275e2be5e4c33f` from PR #236.
- Its Vercel production deployment reached `READY` and matches the `main` revision.
- A runtime-error check over the latest one-hour production window found no active runtime-error group.
- `/health/beta-readiness` reports the private-beta execution and production-transport safety signals as safe while external execution remains disabled.
- Deployed browser-security headers include the established CSP/HSTS/frame/MIME/referrer protections plus popup-compatible COOP, disabled DNS prefetch and Origin-Agent-Cluster isolation.
- Production `/docs`, `/redoc` and `/openapi.json` return 404.
- Google Ads **Explorer Access** is approved for the Cloud project owning the Vexmera OAuth client and is sufficient for the current read-only five-company pilot while its quota and feature set remain adequate.
- A real production Google Ads read-only sync has returned and persisted campaign-level rows without provider warnings. Google Analytics has also returned real rows.
- GA website sessions are translated out of paid-click semantics at the read boundary, preventing them from inflating paid CTR/CPC.
- Meta is connected and the latest verified read-only sync produced a legitimate zero-row empty-data state rather than an authentication/provider error.
- Google/Meta OAuth configuration detection now fails closed on effectively blank values while preserving the existing callback and token-refresh safety wrappers.
- The current Stripe test catalog contains active monthly Start / Growth / Pro prices at 995 / 1,495 / 2,995 SEK with current pricing-version metadata. The test webhook endpoint exists.
- The Stripe sandbox still lacks fresh Checkout/trial/webhook/Customer Portal E2E evidence and currently exposes no Billing Portal configuration.
- The owner-approved Private Beta Customer Portal policy is now fixed: payment-method updates allowed, cancellation allowed at period/trial end, self-service plan changes disabled, no automatic refund rule, and cancellation is separate from account/data deletion.
- Public Privacy and Terms routes are live, but legal entity/contact and longer-lived retention/subprocessor decisions are not final.

## Priority 0: finish Stripe sandbox E2E

Goal: prove the commercial flow without touching live-mode billing.

Completed foundations:

- Start / Growth / Pro is the canonical product model;
- current test prices are independently verified at 995 / 1,495 / 2,995 SEK monthly;
- the canonical catalog verifier rejects live-mode, inactive, wrong-currency, wrong-interval and wrong-amount Price objects;
- Checkout is fail-closed until the current pricing version and required Stripe configuration are reconciled;
- signed webhook handling includes payload/signature limits, idempotency and workspace/customer integrity checks;
- the test webhook endpoint is present for the canonical Vexmera webhook URL;
- the owner-approved Customer Portal policy is recorded in `STRIPE_PORTAL_POLICY.md`;
- application-side plan switching through a second Checkout is blocked while a workspace has an active subscription;
- Customer Portal creation is being pinned to an explicit reviewed configuration id rather than silently inheriting an unknown Stripe default policy.

Remaining gates:

- confirm the deployed Stripe Price environment variables and test secret belong to the same verified sandbox account;
- run `python scripts/verify_stripe_catalog.py` in the configured deployment environment and require `catalog_ok=true`;
- confirm the current pricing-version marker only after catalog verification;
- create the **test-mode Billing Portal configuration** using the already approved policy;
- set the resulting non-secret `STRIPE_BILLING_PORTAL_CONFIGURATION_ID` in the intended test deployment environment;
- run fresh Vexmera Checkout -> remaining trial -> signed webhook -> workspace billing update -> Customer Portal -> safe return;
- verify one idempotent billing projection/event for the intended test workspace;
- keep VAT/tax and live-mode billing as a separate owner/legal/accounting decision.

The currently connected Stripe tool surface can read Billing Portal configurations but does not expose creation/update of them, so that account-side mutation remains an external tooling gate rather than an unresolved product-policy decision.

## Priority 1: authenticated desktop and mobile browser QA

Goal: prove that real users can complete the product journey on the deployed release.

Remaining gates:

- registration and login;
- password reset and session invalidation;
- onboarding completion and post-onboarding routing;
- Google/Meta connector success, legitimate empty-data and safe failure states;
- disconnect and synchronized-history deletion;
- account privacy/deletion preview;
- billing UI and return handling once Stripe E2E is available;
- GA sessions displayed separately from paid-media clicks;
- recommendation-only execution posture;
- mobile navigation, forms, tables, modals and touch targets.

This requires an authenticated interactive browser session. Static HTTP fetches and code inspection are not substitutes.

## Priority 2: legal and pilot operations

Goal: make the private beta supportable and legally reviewable without inventing company facts or retention promises.

Completed foundations:

- public Privacy Policy and Terms routes exist and are linked;
- connector disconnect, synchronized-history deletion, account deletion and consent controls are implemented;
- session lifetime is 14 days;
- password-reset capabilities expire after 60 minutes;
- workspace invites expire after 7 days;
- expired/superseded one-time capabilities are pruned;
- current Neon project point-in-time history is configured for 6 hours, which is infrastructure evidence rather than a universal processor-retention promise;
- pilot runbook, go/no-go checks and release-traceable secrets-safe evidence templates exist.

Remaining owner/legal gates:

- confirm full legal entity/business name, registration details and required postal address;
- choose one verified privacy/support contact and align marketing + legal pages;
- finalize longer-lived retention rules for AI history, synced data, competitor records, feedback, email/provider logs and billing/compliance records;
- verify processor/subprocessor contracts, roles, transfer safeguards and public disclosures;
- complete final Privacy Policy and Beta Terms review;
- decide VAT/tax treatment before live paid launch.

Do not replace the current contact mismatch with an unverified domain alias solely for appearance.

## Google Ads status

Google Ads production access is no longer a five-company pilot blocker. Explorer Access is approved and a real read-only production sync works.

**Basic Access is a future scaling/functionality upgrade, not the current pilot gate.** If Vexmera later needs more than the Explorer quota or Explorer-restricted API functionality, complete the current Google verification/upgrade flow then; do not block the read-only Private Beta on that future scaling step.

For every pilot company, still verify the user's account authorization and perform a fresh read-only sync. A new customer's permission error must never be presented as healthy zero data.

## Working completion estimate

These percentages are planning estimates, not release certification.

- Public website / conversion layer: 94%
- Core application UI and navigation: 92%
- Backend / diagnostics / safety foundations: 97%
- Google + Meta production-read integration readiness: 95%
- Billing sandbox readiness: 85%
- Five-company pilot operations / documentation: 96%
- Production observability and release deployment: 100%
- Final authenticated browser QA: 65%
- Overall private-beta readiness: approximately 94%

The remaining work is concentrated in the Stripe sandbox configuration/E2E, authenticated desktop/mobile QA and final owner/legal decisions rather than missing core product code.

## Immediate next action

1. Require fresh green CI for the explicit Customer Portal policy guardrails.
2. Create the approved Stripe **test-mode** Billing Portal configuration when an authorized write surface is available and set its non-secret configuration id in the intended test deployment.
3. Complete Checkout/trial/webhook/Portal E2E and verify idempotent billing projection.
4. Run full authenticated desktop and mobile QA in an interactive browser session.
5. Finalize verified legal entity/contact details, longer-lived retention/subprocessor decisions and legal review.
6. Start the five-company pilot only after the applicable gates above are clear.
