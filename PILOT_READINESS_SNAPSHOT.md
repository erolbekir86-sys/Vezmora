# Vexmera private beta readiness snapshot

Last reviewed: 2026-09-10

This file is a non-secret operational snapshot for the five-company private beta. It records only evidence that can be safely verified without changing credentials, billing, permissions, domains, DNS, or live advertising settings.

## Verified healthy

- GitHub repository is reachable and writable through the connected GitHub integration; the default branch is `main`.
- Latest observed `main` commit in this refresh is `1df21b62a4b1413eb59b87add2487aee02513df0` (`Prevent caching of API responses`).
- The Python package identifies the product as `vexmera` version `0.6.1`.
- CI/test coverage includes deployment, execution safety, auth/session behavior, connector empty/error states, privacy controls, analytics consent, Google Ads diagnostics, billing alignment, beta readiness, frontend asset smoke coverage, security headers, API cache policy and credential-redaction paths.
- Authentication/session hardening includes secure/HttpOnly/SameSite cookies, Vercel-forced secure cookies, bounded malformed session-cookie input, expired capability cleanup, fail-closed malformed stored password records and authenticated mutation CSRF guards.
- Public and API responses now carry low-risk browser/security hardening, including HSTS in HTTPS production, clickjacking protection, nosniff, strict referrer policy, restricted unused browser permissions and no-store cache policy on the `/api` surface.
- Secret redaction is shared across user-visible HTTP errors, provider diagnostics, persisted worker failures, SMTP failures and execution audit persistence. Delivered transactional email bodies are scrubbed after successful send.
- Public health/readiness diagnostics are minimized in production so they do not expose database paths, provider configuration details or credential-presence information unnecessarily.
- External ad execution and autopilot execution are fail-closed on Vercel Private Beta at both runtime-flag and request-route boundaries.
- Stripe webhook handling validates signed payloads, rejects malformed structures, remains idempotent and rejects oversized payloads before verification work.
- Public frontend smoke coverage verifies that `/` and `/app` return content and referenced local JavaScript/CSS assets are present and non-empty.
- Frontend resilience includes fail-open landing reveal behavior plus consistent loading/error handling for core asynchronous app views.
- Connector empty-state handling distinguishes successful zero-row accounts from provider failures, HTTP errors and missing Google Ads configuration. Provider warnings are preserved instead of being replaced by reassuring empty-state copy.
- Google and Meta read-only connector paths have bounded retry and response-safety hardening; Meta Insights also has bounded pagination with loop/limit protection.
- Google Analytics historical beta rows are translated at the read boundary: GA `sessions` are surfaced as website sessions while the paid-click value is zeroed for those rows, preventing GA sessions from inflating paid-media CPC/CTR calculations without rewriting production history.
- The pilot runbook explicitly requires recommendation-only behavior and forbids autonomous campaign, budget, bid or ad changes.
- Production database intent is confirmed from code: `DATABASE_URL`/`POSTGRES_URL` (Neon/Postgres) is preferred, while Turso is retained as a compatibility fallback.
- Start / Growth / Pro is the current canonical customer-facing and code pricing model at 995 / 1,495 / 2,995 SEK monthly. Checkout remains fail-closed until the current Stripe test-mode catalog and pricing-version marker are independently verified.
- Pilot runbook, secrets-safe per-company evidence template, launch-gap plan and release safety checks exist for the five-company pilot.

## Current blockers requiring manual or external resolution

### 1. Direct Vercel connector visibility

Rechecked during the current hardening cycle: the connected Vercel integration does not currently expose the existing team/project directly to ChatGPT. GitHub-to-Vercel status checks have been usable, so this remains an integration authorization/scope limitation rather than evidence that the project was deleted.

Manual action is only required if direct Vercel logs/project inspection is needed: reconnect or authorize the existing Vercel integration with read access to the current project. Do not change domains, DNS, secrets, credentials, project permissions or production settings as part of this check.

### 2. Google Ads API approval

The Vexmera manager-to-client relationship is recorded as active, but Google Ads Basic Access remains an external prerequisite for normal production-client reads.

Keep all advertising behavior read-only/recommendation-only until Basic Access and a real production read-only sync are independently verified. Do not enable external ad execution, campaign changes, budget changes or bid changes as part of pilot preparation.

### 3. Live connector verification

Automated coverage now distinguishes legitimate empty accounts from provider failures and protects against malformed provider responses without exposing secrets, but a deployed real-account walkthrough is still required for Google Ads and Meta.

Verify that successful empty accounts show a clear empty state, provider/API failures show actionable sanitized diagnostics, and Google Analytics rows continue to show website-session semantics rather than paid-click semantics.

### 4. Stripe sandbox end-to-end verification

The code and public pricing model are aligned, but a fresh account-level Stripe sandbox verification remains an external/manual gate. Required checks include the current Start / Growth / Pro test catalog, pricing-version marker, signed webhook behavior, Checkout/trial flow and Customer Portal behavior.

Do not bypass the checkout safety guard or change Stripe keys, Price IDs, billing configuration or live-mode settings autonomously.

### 5. Legal/pilot sign-off

Before inviting external pilot companies, finalize the Privacy Policy and Beta Terms with concrete legal entity/contact details, retention periods and subprocessor disclosures. Legal review remains a launch gate.

### 6. Final deployed browser QA

Perform one authenticated browser pass on the actual deployed Command Center before the first pilot. Confirm onboarding, loading/empty/error states, connector failure states, disconnect flows, account privacy controls, GA session semantics, recommendation-only behavior, and desktop/mobile rendering.

## Pilot safety gate

Do not start the five-company external pilot until all of the following are true:

- the active production deployment is confirmed and health can be inspected;
- `/health/beta-readiness` reports `private_beta_execution_safe=true`;
- pilot readiness reports no unresolved configuration blockers;
- external execution remains disabled;
- required pilot connectors pass real read-only sync checks;
- legitimate empty connector accounts and provider failures are visually distinguishable in deployed QA;
- GA sessions are presented as website sessions and excluded from paid-click calculations;
- the current Start / Growth / Pro Stripe test catalog is verified before any Checkout test;
- a fresh Stripe sandbox end-to-end test passes if billing is included in the pilot;
- Privacy Policy and Beta Terms are finalized;
- authenticated desktop/mobile browser QA passes.

## Current autonomous-safe work

Without account-owner intervention, continue only with reversible work that is supported by code evidence, including:

1. regression tests and code-quality cleanup;
2. auth/session/CSRF/security-header hardening;
3. secret-redaction and retention minimization;
4. frontend resilience, accessibility and clear loading/empty/error states;
5. read-only connector reliability and sanitized diagnostics;
6. release documentation, QA evidence and five-company pilot preparation;
7. fixes found by CI or static/runtime-safe inspection that do not alter external accounts, billing, DNS, permissions or live advertising behavior.
