# Vexmera private beta readiness snapshot

Last reviewed: 2026-09-12

This file is a non-secret operational snapshot for the five-company private beta. It records only evidence that can be safely verified without changing credentials, billing, permissions, domains, DNS or live advertising settings.

## Verified healthy

- GitHub repository is reachable and writable through the connected GitHub integration; the default branch is `main`.
- The code baseline observed immediately before this documentation refresh was `cecbff7694de15728949f1bd6a4a67bc32a360f9` on `main`.
- Private-beta release packaging now includes the post-170 security work plus the latest auth, request-boundary, secret-redaction and CI dependency-consistency hardening.
- GitHub Actions verification was green for the latest hardening changes: dependency consistency (#173), ordinary API request-body limits (#174), login-only enumeration hardening (#176) and OAuth diagnostic query redaction (#177).
- The GitHub-side Vercel checks for the latest runtime hardening PRs completed successfully with no unresolved preview feedback. This is useful deployment-path evidence, but is not treated as direct runtime observability.
- CI now verifies the installed Python dependency graph with `python -m pip check` before compilation and tests.
- Stripe webhooks have a dedicated 1 MB ASGI streaming/request-body ceiling and fail closed on malformed, negative or duplicate `Content-Length` before buffering.
- Ordinary mutating `/api` requests now have a separate 1 MiB pre-buffer/streaming ceiling, including chunked-body enforcement and fail-closed `Content-Length` validation. Stripe remains on its dedicated limiter.
- Secure session-cookie cleanup is shared by logout and permanent account deletion.
- Successful password reset revokes all existing authenticated sessions atomically with credential rotation.
- Login now reduces the obvious known-vs-unknown account timing signal with equivalent password-KDF work for missing accounts, scoped to the login route only so password-reset behavior is not unintentionally changed.
- Authenticated mutation CSRF protection blocks both cross-site and `same-site` cross-origin browser requests in addition to SameSite cookie protection.
- OAuth callback/provider diagnostic URLs are sanitized for authorization codes, state values, access/refresh tokens and client secrets without hiding ordinary non-URL provider error codes.
- Baseline production security headers include CSP, HSTS on HTTPS runtime, `nosniff`, frame denial, referrer restrictions, permissions policy and no-store handling for sensitive/API responses.
- Public production health responses remain intentionally minimal and do not reveal provider, database, billing, SMTP, OAuth or secret-configuration inventory.
- External marketing execution and Autopilot execution remain fail-closed in Vercel Private Beta; preview/recommendation paths remain available for human review.
- Meta production scope hardening keeps `ads_management` disabled on Vercel. Meta read sync remains based on `ads_read` unless a separate non-production execution scope is explicitly enabled.
- Google/Meta read paths retain bounded retries, input validation, non-redirecting token-bearing transports and sanitized provider-facing diagnostics.
- Connector empty-state handling distinguishes genuine successful zero-row states from configuration/provider failures and preserves actionable sanitized warnings.
- The public marketing page uses illustrative demo metrics and identifies them as demo data.
- Google Analytics session semantics remain explicitly guarded: current GA `sessions` normalization must not be presented as paid-ad clicks or used as paid-media click truth in the pilot.
- The pilot runbook requires recommendation-only behavior and forbids autonomous campaign, budget, bid or ad changes.
- Production database intent remains Neon/Postgres through `DATABASE_URL`/`POSTGRES_URL`, with Turso retained only as legacy compatibility.
- Five-company pilot diagnostics distinguish machine-checkable configuration readiness from manual/external launch gates.
- New Stripe Checkout remains deliberately guarded until the current pricing/catalog version and sandbox evidence are reconciled; no billing configuration was changed during this refresh.

## Current blockers requiring manual or external resolution

### 1. Direct Vercel project/runtime visibility

Rechecked 2026-09-12: the connected Vercel integration can see the `Vezmora` team (`team_ujJMnSfADV4K416z45SV43gL`) but currently enumerates zero projects. A direct lookup of a GitHub-reported preview hostname also returns `Deployment not found` through the connector.

At the same time, GitHub-side Vercel checks for the latest hardening PRs are successful and expose preview-feedback links. Treat this as a connector authorization/visibility mismatch, not proof that the project or deployment is missing.

Manual action only if direct Vercel runtime inspection is required: reconnect/authorize the Vercel integration with access to the existing project. Do not change domains, DNS, secrets, credentials, project settings or production permissions as part of that check.

### 2. Public pricing / backend / Stripe sandbox reconciliation

The current pilot documentation continues to treat Checkout as blocked until the approved Start / Growth / Pro pricing version, backend plan metadata, tests and Stripe sandbox products/prices describe the same verified model.

Do not bypass the checkout safety guard. Do not change Stripe keys, Price IDs, billing settings, bank information or payment configuration autonomously.

### 3. Google Ads API approval

Google Ads Basic Access remains an external prerequisite for normal production-client reads. Test Account Access does not substitute for real production read evidence.

Keep advertising behavior read-only/recommendation-only until Basic Access and a real production read-only sync are independently verified. Do not enable external ad execution, campaign changes, budget changes or bid changes as part of pilot preparation.

### 4. Live connector verification

Automated coverage distinguishes legitimate empty accounts from provider failures without exposing secrets, but a real deployed walkthrough is still required for Google Ads and Meta. Verify that successful empty accounts show a clear empty state and provider/API failures show actionable, sanitized diagnostics.

For Google Analytics, also verify that the sessions-semantics warning is visible and that `source=google_analytics` data is not presented as paid-ad clicks, CPC/CTR input or cross-channel paid-media click totals.

### 5. Google Analytics metric model cleanup

Google Analytics currently requests `sessions` but normalizes that value into Vexmera's generic `clicks` KPI field. Pilot safeguards prevent that value from being treated as paid-ad clicks, but the long-term data model should separate website sessions from advertising clicks.

Do not perform a historical data/schema migration autonomously without migration evidence and explicit compatibility coverage. Until then, incorrect GA click labeling or aggregation is a stop condition for GA analysis in the pilot.

### 6. Stripe sandbox end-to-end verification

After pricing reconciliation is complete, a fresh sandbox verification remains an external/manual gate. Required checks include the approved test catalog, signed webhook behavior, Checkout/trial flow and Customer Portal behavior.

Do not bypass the pricing guard to perform this test early.

### 7. Legal/pilot sign-off

Before inviting external pilot companies, finalize the Privacy Policy and Beta Terms with concrete legal entity/contact details, retention periods and subprocessor disclosures. Legal review remains a launch gate.

### 8. Final deployed browser QA

Perform one authenticated browser pass on the actual deployed Command Center before the first pilot. Confirm onboarding, connector empty/failure states, disconnect flows, account privacy controls, GA metric semantics, recommendation-only behavior and responsive rendering. Also confirm the public marketing page and `/app` in a real browser.

## Pilot safety gate

Do not start the five-company external pilot until all of the following are true:

- the active production deployment is directly confirmed and health/runtime evidence can be inspected;
- `/health/beta-readiness` reports `private_beta_execution_safe=true`;
- `pilot_readiness.configuration_ready=true` with no configuration blockers;
- external execution remains disabled;
- required pilot connectors pass live read-only sync checks;
- legitimate empty connector accounts and provider failures are visually distinguishable in deployed QA;
- GA sessions are not presented or aggregated as paid-ad clicks;
- current pricing, backend plan metadata, billing tests and Stripe sandbox catalog are reconciled before any new Checkout test;
- a fresh Stripe sandbox end-to-end test passes if billing is included in the pilot;
- Privacy Policy and Beta Terms are finalized;
- authenticated browser QA passes.

## Next safe autonomous work

While direct Vercel project visibility remains unavailable, continue only with reversible code quality, diagnostics, tests, documentation, onboarding and beta-safety hardening that does not alter live ad execution, billing, secrets, permissions, DNS or customer data.

When direct Vercel visibility becomes available, the next low-risk checks are:

1. inspect production runtime errors and non-secret health diagnostics;
2. confirm the active production deployment revision matches GitHub `main`;
3. verify execution-safety diagnostics remain fail-closed;
4. inspect unresolved Vercel toolbar feedback;
5. run authenticated browser QA on the deployed Command Center;
6. update this snapshot only when evidence changes.
