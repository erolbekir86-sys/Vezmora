# Vexmera 0.6.1 Private Beta — Deployment Release

Built on Vexmera 0.6 with the beta product features intact, plus:

- Vercel FastAPI entrypoint and `vercel.json`
- serverless-safe execution mode
- authenticated daily maintenance cron
- immediate processing of critical user-triggered jobs in serverless mode
- Neon/Postgres production persistence, with legacy Turso compatibility retained
- inserted-ID handling that does not rely on remote `lastrowid`
- StripeClient-based subscription billing integration
- 14-day first-customer subscription trial flow
- Stripe trial status and trial end synchronized by signed webhook handling
- Stripe Customer Portal integration
- verified **test-mode** Vexmera Starter, Growth and Scale catalog for the currently connected Stripe sandbox
- safe Stripe catalog preflight that validates active monthly SEK prices and expected amounts without printing secrets or IDs
- Stripe webhook payload and signature-input bounds before signature verification
- Stripe webhook request-body protection at the ASGI boundary, including a 1 MB streaming limit and fail-closed handling of malformed, negative or duplicate `Content-Length` headers before body buffering
- ordinary mutating `/api` requests protected by a separate 1 MiB pre-buffer/streaming body ceiling, with malformed, negative and duplicate `Content-Length` rejected before application parsing; Stripe retains its dedicated webhook limiter
- Stripe webhook retry safety that keeps completed event IDs idempotent while leaving transient billing-state failures retryable until the local projection succeeds
- Google/Meta private-beta connector work with external execution kept behind explicit safety gates
- bounded provider transport handling with customer-visible transport errors sanitized before rendering
- explicit no-redirect transport for Google authorization-code exchange, access-token refresh, Analytics/Ads reads, Ads diagnostics and provider-token revocation
- Google Analytics property-ID and Google Ads API-version validation before provider URL construction
- explicit no-redirect transport for Meta OAuth exchange, ad-account discovery, account probe, campaign discovery and the canonical Insights read path
- strict Meta ad-account and Graph-version validation before token-bearing URL construction, plus mapped/sanitized provider errors instead of raw Meta messages
- Meta paging restricted to HTTPS `graph.facebook.com` URLs without embedded credentials, with bounded retries, page limits and repeated-page detection
- connector-state integrity that keeps provider/configuration failures out of healthy empty-data states while preserving genuine zero-row and partial-data states
- baseline runtime CSP plus HSTS, no-store, referrer, frame, MIME-sniffing and browser capability hardening
- server-side CSRF defence-in-depth for authenticated state-changing API requests in addition to SameSite session cookies, including fail-closed blocking of `same-site` but cross-origin browser mutations from sibling origins
- secure session-cookie cleanup shared by normal logout and permanent account deletion so production `Secure` cookie attributes remain aligned when authentication state is cleared
- successful password reset treated as credential rotation, with all previously authenticated sessions revoked atomically with the password update
- login-only account-enumeration timing hardening that adds equivalent password-KDF work for unknown accounts without changing password-reset or other email-lookup flows
- diagnostic secret redaction extended to OAuth callback/provider URL capabilities such as authorization `code`, `state`, access/refresh tokens and client secrets while preserving ordinary non-URL error-code context
- API auth-surface regression coverage so newly introduced `/api/...` routes cannot silently become public unless explicitly allowlisted
- repository secret-hygiene regression coverage for common provider-key and webhook-secret formats
- AI evidence-boundary hardening that treats company profiles, business memory, connector data, competitor content, web-derived text and saved notes as untrusted data rather than instructions, while preserving human approval gates and secret-handling rules
- a minimal public production health/privacy contract that exposes deployment identity without provider, database, billing, SMTP, OAuth or secret-configuration inventory
- CI supply-chain hardening and removal of the obsolete write workflow
- CI dependency-consistency verification with `python -m pip check` after installation, before compile and test stages
- release-version consistency checks so package/app/release metadata cannot drift silently
- premium Vexmera marketing-site and Command Center polish aligned to the same pricing, product names and private-beta language
- Swedish-first Command Center customer copy with Core, Pulse, Launch and Autopilot retained as product names
- explicit first-use dashboard guidance and clear empty-state handling for customers without connected KPI data
- consolidated five-company pilot go/no-go documentation separating machine-checkable safety from required human/manual evidence
- Python 3.12+ deployment target
- automated Python tests plus syntax validation for all shipped frontend JavaScript in GitHub Actions

## Important private-beta boundaries

- The public marketing page uses illustrative demo metrics and labels them as demo data.
- Google Ads and Meta Ads are private-beta integrations, not general-availability claims.
- External marketing execution and Autopilot execution remain disabled by default and require separate server-side enablement.
- Google connector transport hardening is code/CI verified, but Google Ads Basic Access, direct deployed runtime inspection and live read-only account evidence remain external/manual pilot gates.
- Meta connector transport hardening is code/CI verified across OAuth exchange, discovery/probe/campaign reads and the canonical Insights path, but direct deployed runtime inspection and live read-only account evidence remain manual pilot gates.
- Stripe request-body and webhook retry hardening are code/CI verified, but fresh sandbox Checkout/webhook evidence is still part of manual pilot validation before billing is treated as pilot-ready.
- Stripe live mode is **not** enabled by these release notes. The connected sandbox catalog is test-only, and deployment Price IDs/webhook configuration must be reconciled before a fresh end-to-end Checkout test.
- VAT/tax handling, final legal terms, the canonical production domain, Google Ads Basic Access, production runtime observability and the five-company pilot remain launch work.
- The GitHub-side Vercel checks for the latest hardening PRs are green, but the connected Vercel integration currently cannot enumerate the project or directly inspect those deployments. Treat direct runtime/deployment inspection as a separate unresolved evidence gate.

## Current release verification posture

The repository now distinguishes three different kinds of evidence:

1. **Code/CI evidence** — automated tests and static/runtime contract checks in GitHub Actions.
2. **Deployment evidence** — direct evidence that a specific Vercel Preview/Production deployment is ready and inspectable; a GitHub-side Vercel check alone is not treated as full runtime observability.
3. **Pilot/manual evidence** — authenticated browser QA, live read-only connector checks, legal/privacy review, pricing/catalog reconciliation, prompt-injection boundary checks using non-sensitive test text, fresh Stripe sandbox evidence, and the documented five-company pilot checklist.

A green CI run alone does not substitute for deployment or pilot/manual evidence. A successful provider read in one environment also does not prove that a different account, OAuth grant, manager hierarchy or provider-access level is ready.

Secrets and credentials are never intentionally committed to the repository. External OpenAI/Google/Meta/SMTP/Stripe services still require the correct environment configuration in the active deployment.
