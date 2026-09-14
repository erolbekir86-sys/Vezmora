# Vexmera launch gap plan

Last reviewed: 2026-09-14

This document tracks the shortest safe path from the current build to a five-company private beta. It intentionally excludes changes to live ad execution, campaign budgets, bids, live-mode billing, secrets, permissions, domains, DNS or customer data.

## How to read this file

Do not use this document alone as a release pointer. Before every launch check, verify the current `main` SHA, open pull requests, GitHub Actions status and the active production deployment. Code/CI evidence, deployed-runtime evidence and authenticated browser evidence are separate gates.

## Current verified position

- Direct Vercel project/runtime inspection is working again.
- Production serves Vexmera over HTTPS and `/health/runtime` identified revision `009a8bb07397589b509afef6599409478f4295bc` during the latest check.
- `/health/beta-readiness` reports the private-beta execution and production-transport safety signals as safe while external execution remains disabled.
- Current production runtime inspection found no active runtime-error group for the checked release window.
- Production `/docs`, `/redoc` and `/openapi.json` return 404.
- Google Ads **Explorer Access** was approved for the Cloud project owning the Vexmera OAuth client on 2026-09-12. Explorer is a production access level and is sufficient for the current read-only five-company pilot while its quota and feature set remain adequate.
- A real production Google Ads read-only sync has returned and persisted campaign-level rows without provider warnings. Google Analytics has also returned real rows.
- GA website sessions are translated out of paid-click semantics at the read boundary, preventing them from inflating paid CTR/CPC.
- The Google manager-to-client relationship is recorded as accepted and active, and successful production reads provide practical evidence that the current account path works.
- Meta is connected and the latest verified read-only sync produced a legitimate zero-row empty-data state rather than an authentication/provider error.
- The current Stripe test catalog contains active monthly Start / Growth / Pro prices at 995 / 1,495 / 2,995 SEK with the current pricing-version metadata. The test webhook endpoint exists.
- Stripe still lacks fresh Checkout/trial/webhook/Customer Portal E2E evidence, and the connected sandbox currently has no Billing Portal configuration.
- Public Privacy and Terms routes are live, but legal entity/contact and longer-lived retention/subprocessor decisions are not final.
- PR #228 contains the current edge-header parity change plus this evidence refresh. A fresh green CI run is required after the documentation commits before merge.

## Priority 0: merge and verify the current release candidate

Goal: ensure the reviewed hardening is actually on `main` and deployed.

Remaining gates:

- require a fresh green Vexmera CI run for the current PR #228 head;
- review the final PR diff and merge it to `main`;
- confirm the resulting production revision and runtime safety after deployment;
- keep external advertising execution and Autopilot execution disabled.

The connected GitHub action is currently blocked from performing the final merge by an external safety control, so the final merge may require the repository owner to click Merge after CI is green.

## Priority 1: finish Stripe sandbox E2E

Goal: prove the commercial flow without touching live-mode billing.

Completed foundations:

- Start / Growth / Pro is the canonical product model;
- current test prices are independently verified at 995 / 1,495 / 2,995 SEK monthly;
- the canonical catalog verifier rejects live-mode, inactive, wrong-currency, wrong-interval and wrong-amount Price objects;
- Checkout is fail-closed until the current pricing version and required Stripe configuration are reconciled;
- signed webhook handling includes payload/signature limits, idempotency and workspace/customer integrity checks;
- the test webhook endpoint is present for the canonical Vexmera webhook URL.

Remaining gates:

- confirm the deployed Stripe Price environment variables and test secret belong to the same verified sandbox account;
- run `python scripts/verify_stripe_catalog.py` in the configured deployment environment and require `catalog_ok=true`;
- confirm the current pricing-version marker only after catalog verification;
- create or intentionally configure a **test-mode Billing Portal configuration** with owner-approved cancellation/plan/payment-method policy;
- run fresh Vexmera Checkout -> remaining 14-day trial -> signed webhook -> workspace billing update -> Customer Portal -> safe return;
- verify one idempotent billing projection/event for the intended test workspace;
- keep VAT/tax and live-mode billing as a separate owner/legal/accounting decision.

## Priority 2: authenticated desktop and mobile browser QA

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

## Priority 3: legal and pilot operations

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

**Basic Access is a future scaling/functionality upgrade, not the current pilot gate.** Google retired the legacy pending-application workflow on 2026-09-09. If Vexmera later needs more than the Explorer quota or Explorer-restricted API functionality, complete OAuth Brand Verification and use the current Cloud Console upgrade flow.

For every pilot company, still verify the user's account authorization and perform a fresh read-only sync. A new customer's permission error must never be presented as healthy zero data.

## Working completion estimate

These percentages are planning estimates, not release certification.

- Public website / conversion layer: 94%
- Core application UI and navigation: 92%
- Backend / diagnostics / safety foundations: 97%
- Google + Meta production-read integration readiness: 95%
- Billing sandbox readiness: 85%
- Five-company pilot operations / documentation: 95%
- Production observability: 95%
- Final authenticated browser QA: 65%
- Overall private-beta readiness: approximately 93%

The remaining work is concentrated in PR merge/deployment confirmation, Stripe sandbox E2E, authenticated desktop/mobile QA and final owner/legal decisions rather than missing core product code.

## Immediate next action

1. Get a fresh green CI result on the current PR #228 head and merge it.
2. Confirm the resulting production revision and safety flags.
3. Configure the Stripe **test-mode** Billing Portal only after the owner selects the intended portal policy, then complete Checkout/trial/webhook/Portal E2E.
4. Run full authenticated desktop and mobile QA in an interactive browser session.
5. Finalize verified legal entity/contact details, longer-lived retention/subprocessor decisions and legal review.
6. Start the five-company pilot only after the applicable gates above are clear.
