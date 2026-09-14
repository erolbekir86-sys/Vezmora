# Vexmera private beta readiness snapshot

Last reviewed: 2026-09-14

This is a non-secret operational snapshot for the five-company private beta. It records evidence that can be verified safely without changing credentials, billing, permissions, domains, DNS or live advertising settings.

## Current release baseline

The latest verified production `main` baseline is merge commit `e2ec57d7061e6639dd76c00458e2cda8436de02d`, which merged PR #228 after Vexmera CI #1418 completed successfully.

PR #228's runtime change mirrors the already-verified application browser-security headers at Vercel's edge/static layer and adds regression coverage. The merged release also refreshes the operational evidence for Vercel, Google/Meta, Stripe and legal/pilot gates.

## Verified healthy from code, CI, deployment and live read-only evidence

- Vexmera CI #1418 passed on the final PR #228 head before merge.
- Production deployment for merge commit `e2ec57d7061e6639dd76c00458e2cda8436de02d` reached Vercel `READY` and is attached to `vexmera.com`.
- `/health/runtime` reports deployment revision `e2ec57d7061e6639dd76c00458e2cda8436de02d`.
- `/health/beta-readiness` reports `private_beta_execution_safe=true` and `production_transport_safe=true`.
- External marketing execution, Autopilot execution and Meta execution scope remain disabled.
- Current production runtime inspection found no active runtime-error group in the post-deploy check window.
- Deployed responses include `Cross-Origin-Opener-Policy: same-origin-allow-popups`, `X-DNS-Prefetch-Control: off` and `Origin-Agent-Cluster: ?1` in addition to the established CSP/HSTS/frame/MIME/referrer protections.
- Production `/docs`, `/redoc` and `/openapi.json` return 404 and do not expose the framework documentation surface.
- Session, CSRF, one-time capability, secret-redaction, webhook-integrity, transport logging and public-health hardening remain covered by regression tests.
- Stripe webhook processing verifies signatures, bounds payload/header size, records events idempotently and rejects workspace/customer ownership mismatches before billing mutation.
- The approved Stripe **test-mode** catalog contains active monthly Start / Growth / Pro prices at 995 / 1,495 / 2,995 SEK with current pricing-version metadata.
- The Stripe test webhook endpoint exists for the canonical Vexmera webhook URL.
- Google Ads API **Explorer Access** was approved for the Cloud project owning the Vexmera OAuth client on 2026-09-12. Explorer is a production access level and is sufficient for the current read-only five-company pilot while its quota and feature set remain adequate.
- A real production Google Ads read-only sync has succeeded and persisted campaign-level rows without provider warnings or API errors.
- Google Analytics has also persisted real rows. GA sessions are translated at the read boundary so they do not inflate paid-ad clicks, CTR or CPC.
- Meta is connected and the latest verified read-only sync produced a legitimate zero-row result classified as an empty-data state rather than an authentication/provider failure.
- Both Google and Meta connector state handling distinguish verified empty data from provider/configuration errors.
- The manager-to-client Google Ads relationship is recorded as accepted and active, and the successful live read provides practical evidence that the intended account is reachable through the deployed OAuth path.
- Public Privacy and Terms routes are reachable over HTTPS and receive normal security headers.
- Production onboarding records exist and completed onboarding has been observed in the production database.

## Evidence boundary

Vexmera separates three evidence classes:

1. **Code/CI evidence** - automated tests, syntax checks, dependency consistency and regression coverage.
2. **Deployment/runtime evidence** - direct evidence that the intended Vercel deployment is active and serving the expected revision.
3. **Pilot/manual evidence** - authenticated browser walkthroughs, fresh billing completion evidence and final legal/owner decisions.

A green CI run does not substitute for browser QA, and a successful read-only provider sync does not authorize external campaign mutation.

## Remaining blockers

### 1. Stripe fresh sandbox E2E and Customer Portal configuration

The Stripe sandbox catalog and webhook endpoint are present, but the connected sandbox still has no completed Vexmera Checkout evidence from the latest verification: no Checkout Sessions, Customers or Subscriptions were found, and no production-database billing events were present.

The Stripe sandbox also had no Billing Portal configuration. Therefore Customer Portal E2E cannot be declared green yet.

Required evidence before billing-enabled pilot onboarding:

1. create or verify an intentional **test-mode** Billing Portal configuration;
2. run Vexmera Checkout against the canonical Start / Growth / Pro test catalog;
3. complete the remaining private-beta trial Checkout using Stripe test data;
4. verify the signed webhook updates only the intended test workspace and records one idempotent billing event;
5. open Customer Portal for the attached test customer and return safely to Vexmera;
6. verify billing state in the UI after reload.

The Portal's cancellation, plan-change and payment-method policy is an owner/business decision. Do not modify live-mode payment settings, bank details, tax configuration, KYC or real customer billing as part of this verification.

### 2. Final authenticated browser QA

A full browser walkthrough is still required on the deployed Command Center:

- registration and login;
- password reset and session invalidation;
- onboarding completion and post-onboarding routing;
- Google and Meta connector success, legitimate empty data and safe failure states;
- disconnect and synchronized-history deletion controls;
- billing UI, Checkout return handling and Customer Portal once Stripe E2E is available;
- account privacy/deletion preview;
- GA sessions presented separately from paid-ad clicks;
- mobile viewport navigation, forms, tables and modals;
- recommendation-only execution posture.

This gate requires an authenticated interactive browser session. Static fetches and API/code inspection are not a substitute.

### 3. Legal and privacy sign-off

Engineering can verify product behavior, but final legal readiness still requires owner/legal decisions that must not be invented in code:

- legal entity name and registration details;
- postal/registered address where required;
- one verified privacy/support contact channel;
- concrete longer-lived retention rules that match actual infrastructure behavior;
- verified subprocessor/contract/transfer disclosures;
- final Privacy Policy and Beta Terms review;
- VAT/tax treatment before live paid launch.

A public contact inconsistency remains: the marketing footer and published legal pages do not currently use one verified contact address. Do not replace it with an unverified domain alias merely for appearance.

## Google Ads access interpretation

Basic Access is **not** a blocker for the current five-company read-only pilot. Explorer Access already permits production-account requests and supports the reporting pattern Vexmera currently uses. Basic becomes a scaling or functionality upgrade when the Explorer quota is insufficient or Vexmera needs Explorer-restricted API functionality.

Google retired the legacy Basic application path on 2026-09-09. Any future Basic upgrade must follow the current Cloud Console flow and requires OAuth Brand Verification first. The old application must not be represented as pending review.

## Pilot safety gate

Do not start a billing-enabled five-company external pilot until all of the following are true:

- the intended production revision is directly confirmed;
- `/health/beta-readiness` continues to report safe execution and transport;
- external execution remains disabled;
- required pilot connectors pass read-only checks for each pilot account;
- legitimate empty accounts and provider failures remain distinguishable;
- GA sessions are not presented or aggregated as paid-ad clicks;
- fresh Stripe sandbox Checkout/trial/webhook/Customer Portal evidence passes if billing is included in the pilot;
- Privacy Policy and Beta Terms are finalized with verified entity/contact details;
- authenticated desktop and mobile browser QA passes.

The release-candidate merge/deployment gate is now complete for the current baseline. A non-billing pilot can proceed without live payment activation only if the pilot terms and product UI accurately reflect that billing is not enabled.

## Safe autonomous work remaining

Safe autonomous work can continue on reversible code quality, tests, diagnostics, documentation, onboarding, read-only connector reliability and beta-safety hardening. Do not alter live ads, campaign budgets/bids, DNS/domain ownership, credentials/secrets, payment/bank details, KYC or external account permissions.
