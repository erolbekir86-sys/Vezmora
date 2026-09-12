# Vexmera private beta readiness snapshot

Last reviewed: 2026-09-12

This is a non-secret operational snapshot for the five-company private beta. It records evidence that can be verified safely without changing credentials, billing, permissions, domains, DNS or live advertising settings.

## Current code baseline

The latest verified `main` baseline at this refresh is `f66299775e85835af5ec8c46c4985ffd7573c0a6`.

Recent merged hardening includes:

- public auth IP burst limiting on Vercel for login, registration and password-reset POSTs;
- login-only account-enumeration timing equalization;
- PBKDF2-HMAC-SHA256 upgraded to a versioned 600,000-iteration record for new and rotated credentials;
- legacy 310,000-iteration password records remain compatible and are opportunistically rehashed to the current policy after a successful login using compare-and-set semantics;
- password reset continues to revoke all existing authenticated sessions atomically with credential rotation;
- active sessions are bounded to the 20 newest sessions per user after expired-session pruning;
- Origin / Fetch Metadata protection now covers public browser login, registration and password-reset POSTs as well as authenticated state-changing API requests;
- ordinary mutating API requests have a separate 1 MiB streaming/pre-buffer body ceiling, while Stripe retains its dedicated webhook limiter;
- OAuth diagnostic URLs redact authorization code/state/token/client-secret capabilities;
- reset/invite emails fail closed on Vercel unless the canonical app URL is explicitly HTTPS;
- Stripe Checkout and Customer Portal return URLs fail closed on Vercel unless the canonical app URL is explicitly HTTPS;
- Google and Meta production OAuth redirect URIs must exactly match the canonical HTTPS app origin plus the expected provider callback path, otherwise that connector fails closed in the process;
- transactional email uses certificate-verifying STARTTLS and Vercel rejects explicitly disabled STARTTLS;
- deployment preflight and `/health/beta-readiness` now agree that production transport is unsafe when SMTP is configured but STARTTLS is disabled;
- CI verifies the installed dependency graph with `python -m pip check` before compile/tests and includes bounded dependency-update checks.

## Verified healthy from code and CI

- GitHub repository access is healthy and the default branch is `main`.
- The hardening PRs described above passed the repository CI before merge.
- External marketing execution and Autopilot execution remain fail-closed for Vercel Private Beta.
- Meta production scope hardening keeps `ads_management` disabled on Vercel.
- Google/Meta token-bearing network paths retain bounded retries, provider/input validation, no-redirect transport where required and sanitized customer-visible failures.
- OAuth state is single-use, provider-scoped, bounded and stored hashed for newly issued state values.
- Password-reset tokens and workspace invites are hashed one-time capabilities and newer reset/invite issuance supersedes older outstanding capabilities for the same target where appropriate.
- Session cookies remain HttpOnly, SameSite and Secure on Vercel; logout/account deletion clear them with aligned attributes.
- API auth-surface tests prevent newly introduced `/api/...` endpoints from silently becoming public unless deliberately allowlisted.
- Public production health/readiness responses remain intentionally minimal; they do not expose provider credentials, database connection strings, SMTP credentials, OAuth secrets or Stripe identifiers.
- Stripe webhook payload/signature bounds and signed-event idempotency protections remain in place.
- Public auth inputs are bounded before KDF/token processing: login/register passwords max out at 200 characters and reset tokens at 300 characters.
- Competitor scanning retains SSRF controls for scheme, DNS resolution, public IPs, redirects and response-size limits.
- Repository dynamic SQL identified during this review remains limited to fixed allowlists/internal field construction rather than direct user-controlled SQL fragments.
- The public marketing page uses illustrative demo metrics and identifies them as demo data.
- The pilot remains recommendation-only; external campaign, budget, bid and ad mutations are not part of the approved private-beta posture.

## Evidence boundary

Vexmera deliberately separates three evidence classes:

1. **Code/CI evidence** — automated tests, syntax checks, dependency consistency and security-contract regression coverage.
2. **Deployment/runtime evidence** — direct evidence that the intended Vercel deployment is active, inspectable and serving the expected revision.
3. **Pilot/manual evidence** — authenticated browser QA, live read-only connector checks, current Stripe sandbox E2E evidence, legal/privacy review and external provider approvals.

A green CI run does not substitute for direct deployed-runtime evidence. A GitHub-side Vercel check is useful deployment-path evidence, but it is not treated as full production observability.

## Current blockers requiring manual or external resolution

### 1. Direct Vercel project/runtime visibility

The connected Vercel integration can see the Vezmora team but currently does not enumerate the existing project. Direct project/deployment/runtime inspection therefore remains unavailable through that connector.

GitHub-side Vercel checks have continued to provide preview/deployment-path evidence, so this visibility problem is not treated as proof that the project is missing. Direct runtime observability remains a manual launch gate.

Do not change domains, DNS, credentials, secrets or project permissions merely to satisfy this document. Re-authorize the Vercel connection only when direct project inspection is intentionally performed.

### 2. Stripe pricing/catalog reconciliation and fresh sandbox E2E

Keep Checkout blocked until the approved Start / Growth / Pro public model, backend metadata, tests and Stripe **test-mode** catalog describe the same verified prices and pricing-version marker.

After reconciliation, perform a fresh sandbox Checkout/trial/webhook/Customer Portal pass. Do not autonomously change Stripe keys, Price IDs, products, bank information, tax configuration or live-mode settings.

### 3. Google Ads external access

Google Ads Basic Access and any required manager/client-account relationship remain external prerequisites. Test Account Access is not proof of normal production-client read access.

Keep Google advertising behavior read-only/recommendation-only until a real deployed read-only sync is independently verified.

### 4. Live Google/Meta connector verification

Code distinguishes healthy empty accounts from provider/configuration failures, but a deployed authenticated walkthrough is still required for real pilot accounts. Confirm success, empty-data and failure states using non-sensitive evidence.

### 5. Google Analytics metric-model cleanup

Current safeguards prevent GA `sessions` from being presented as paid-ad click truth, but the long-term model should represent website sessions separately from advertising clicks. Until then, incorrect GA click labeling or cross-channel aggregation remains a stop condition.

### 6. Legal and privacy sign-off

Finalize Privacy Policy and Beta Terms with the real legal entity/contact details, retention periods and subprocessor disclosures. Legal review remains a launch gate.

### 7. Final deployed browser QA

Perform an authenticated browser pass on the actual deployed Command Center. At minimum verify onboarding, login/reset, connector success/empty/failure states, disconnect, account privacy controls, GA semantics, recommendation-only behavior, responsive rendering and the public marketing page.

## Pilot safety gate

Do not start the five-company external pilot until all of the following are true:

- the intended production deployment is directly confirmed and its revision/runtime health can be inspected;
- `/health/beta-readiness` reports `private_beta_execution_safe=true` and `production_transport_safe=true`;
- configuration readiness has no machine-checkable blockers;
- external execution remains disabled;
- required pilot connectors pass live read-only checks;
- legitimate empty accounts and provider failures are visually distinguishable in deployed QA;
- GA sessions are not presented or aggregated as paid-ad clicks;
- the current Stripe sandbox catalog is reconciled and fresh E2E billing evidence passes if billing is included in the pilot;
- Privacy Policy and Beta Terms are finalized;
- authenticated browser QA passes.

## Safe autonomous work remaining

While direct Vercel project visibility is unavailable, safe autonomous work remains limited to reversible code quality, tests, diagnostics, documentation, onboarding, read-only connector reliability and beta-safety hardening that does not alter live ads, billing accounts, secrets, permissions, DNS or customer data.

When direct Vercel visibility becomes available, the next low-risk checks are:

1. inspect production runtime errors and non-secret health diagnostics;
2. confirm the active deployment revision matches GitHub `main`;
3. verify execution, transport and public-readiness flags remain fail-closed;
4. inspect unresolved deployment feedback;
5. run authenticated browser QA on the deployed Command Center;
6. update this snapshot only from newly observed evidence.
