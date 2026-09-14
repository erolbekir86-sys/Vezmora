# Vexmera 0.6.1 Private Beta - Deployment Release

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
- safe Stripe catalog preflight for the current Start / Growth / Pro test-mode target without printing secrets or identifiers
- Stripe webhook payload and signature-input bounds before signature verification
- Stripe webhook request-body protection at the ASGI boundary, including a 1 MB streaming limit and fail-closed handling of malformed, negative or duplicate `Content-Length` headers before body buffering
- ordinary mutating `/api` requests protected by a separate 1 MiB pre-buffer/streaming body ceiling, with malformed, negative and duplicate `Content-Length` rejected before application parsing; Stripe retains its dedicated webhook limiter
- Stripe webhook retry safety that keeps completed event IDs idempotent while leaving transient billing-state failures retryable until the local projection succeeds
- Stripe Checkout success/cancel URLs and Billing Portal return URLs fail closed on Vercel unless `VEZMORA_APP_URL` is explicitly HTTPS; local development retains its localhost fallback
- Google/Meta private-beta connector work with external execution kept behind explicit safety gates
- bounded provider transport handling with customer-visible transport errors sanitized before rendering
- explicit no-redirect transport for Google authorization-code exchange, access-token refresh, Analytics/Ads reads, Ads diagnostics and provider-token revocation
- Google Analytics property-ID and Google Ads API-version validation before provider URL construction
- explicit no-redirect transport for Meta OAuth exchange, ad-account discovery, account probe, campaign discovery and the canonical Insights read path
- strict Meta ad-account and Graph-version validation before token-bearing URL construction, plus mapped/sanitized provider errors instead of raw Meta messages
- Meta paging restricted to HTTPS `graph.facebook.com` URLs without embedded credentials, with bounded retries, page limits and repeated-page detection
- production Google/Meta redirect URIs must exactly match the canonical HTTPS Vexmera origin plus the expected provider callback path or the connector fails closed in that runtime
- connector-state integrity that keeps provider/configuration failures out of healthy empty-data states while preserving genuine zero-row and partial-data states
- baseline runtime CSP plus HSTS, no-store, referrer, frame, MIME-sniffing and browser capability hardening
- server-side Origin / Fetch Metadata CSRF defence-in-depth for authenticated state-changing API requests in addition to SameSite session cookies, including fail-closed blocking of `same-site` but cross-origin browser mutations from sibling origins
- the same browser-origin boundary now covers public login, registration and password-reset POSTs, reducing login-CSRF/cross-origin auth abuse without breaking non-browser clients that send no browser Origin/Fetch Metadata
- secure session-cookie cleanup shared by normal logout and permanent account deletion so production `Secure` cookie attributes remain aligned when authentication state is cleared
- successful password reset treated as credential rotation, with all previously authenticated sessions revoked atomically with the password update
- login-only account-enumeration timing hardening that adds equivalent password-KDF work for unknown accounts without changing password-reset or other email-lookup flows
- process-local IP abuse limiting for public login, registration and password-reset POST endpoints on Vercel, with `Retry-After` and no-store responses; this is defense in depth and does not replace distributed edge controls
- versioned PBKDF2-HMAC-SHA256 password records for new/rotated credentials using a 600,000-iteration work factor, while historical 310,000-iteration records remain verifiable with timing padding
- successful login of a legacy 310,000-iteration account opportunistically rehashes it to the current 600,000-iteration format using compare-and-set semantics, without revoking unrelated active sessions or overwriting concurrent credential changes
- active session capabilities bounded to the 20 newest sessions per user after expired-session pruning, retaining multi-device use without unbounded capability growth
- transactional SMTP transport fails closed on Vercel when STARTTLS is disabled, validates SMTP ports before network I/O and uses a certificate-verifying default TLS context before reset/invite mail or SMTP credentials are sent
- reset/invite capability links fail closed on Vercel unless `VEZMORA_APP_URL` is explicitly HTTPS, preventing a production fallback to `http://localhost:8000`
- deployment preflight and live `/health/beta-readiness` agree that production transport is unsafe when SMTP is configured but STARTTLS is disabled; the public health surface remains aggregate/minimal and does not expose SMTP configuration details
- diagnostic secret redaction extended to OAuth callback/provider URL capabilities such as authorization `code`, `state`, access/refresh tokens and client secrets while preserving ordinary non-URL error-code context
- API auth-surface regression coverage so newly introduced `/api/...` routes cannot silently become public unless explicitly allowlisted
- repository secret-hygiene regression coverage for common provider-key and webhook-secret formats
- AI evidence-boundary hardening that treats company profiles, business memory, connector data, competitor content, web-derived text and saved notes as untrusted data rather than instructions, while preserving human approval gates and secret-handling rules
- a minimal public production health/privacy contract that exposes deployment identity and aggregate safety evidence without provider, database, billing, SMTP, OAuth or secret-configuration inventory
- pilot/runtime/legal preflight HTTP evidence bound to a plain HTTPS origin with redirects rejected, public response buffering capped at 1 MiB and ambiguous targets rejected before network I/O
- CI supply-chain hardening and removal of the obsolete write workflow
- CI dependency-consistency verification with `python -m pip check` after installation, before compile and test stages
- bounded scheduled dependency-update checks so dependency drift is surfaced without granting broad workflow write behavior
- release-version consistency checks so package/app/release metadata cannot drift silently
- premium Vexmera marketing-site and Command Center polish aligned to the same pricing, product names and private-beta language
- Swedish-first Command Center customer copy with Core, Pulse, Launch and Autopilot retained as product names
- explicit first-use dashboard guidance and clear empty-state handling for customers without connected KPI data
- consolidated five-company pilot go/no-go documentation separating machine-checkable safety from required human/manual evidence
- Python 3.12+ deployment target
- automated Python tests plus syntax validation for all shipped frontend JavaScript in GitHub Actions

## Important private-beta boundaries

- The public marketing page uses illustrative demo metrics and labels them as demo data.
- Google Ads and Meta Ads remain private-beta integrations, not general-availability claims.
- External marketing execution and Autopilot execution remain disabled by default and require separate explicit production review before any future enablement.
- Google Ads **Explorer Access** was approved for the Cloud project owning the Vexmera OAuth client on 2026-09-12. A real production read-only sync has returned campaign-level rows without provider warnings. Basic Access is a future quota/functionality upgrade, not a current five-company read-only pilot blocker.
- Meta read-only access has been verified against a connected account, including a legitimate zero-row empty-data result that is kept distinct from provider/authentication failure.
- Direct Vercel production project/runtime inspection is available again. The current PR #228 release was merged after green CI, deployed to production, reached `READY`, and serves the merged `main` revision with safe private-beta execution/transport flags and no active runtime-error group in the post-deploy check window.
- Production FastAPI documentation routes are hidden and return 404.
- Stripe transport, request-body and webhook hardening are code/CI verified, and the current Start / Growth / Pro test catalog plus test webhook endpoint have been independently observed. Fresh Checkout/trial/webhook/Customer Portal E2E is still required before billing is treated as pilot-ready.
- The connected Stripe sandbox had no Billing Portal configuration at the latest check. Portal cancellation, plan-change and payment-method policy remains an owner/business decision.
- Stripe live mode is **not** enabled by these release notes. Test-mode evidence must not be treated as live billing approval.
- VAT/tax handling, final legal terms, authenticated desktop/mobile browser QA and the five-company pilot remain launch work.
- Published marketing/legal contact details are not yet normalized to one verified support/privacy channel. Do not invent a domain alias or legal entity detail merely to close the checklist.

## Current release verification posture

The repository distinguishes three kinds of evidence:

1. **Code/CI evidence** - automated tests, dependency consistency, syntax checks and static/runtime contract checks in GitHub Actions.
2. **Deployment evidence** - direct evidence that a specific Vercel Preview/Production deployment is ready, serving the intended revision and inspectable at runtime.
3. **Pilot/manual evidence** - authenticated browser QA, per-pilot read-only connector checks, legal/privacy review, pricing/environment reconciliation, fresh Stripe sandbox E2E and the five-company pilot checklist.

A green CI run alone does not substitute for deployment or pilot/manual evidence. A successful provider read for one account also does not prove a different customer's OAuth grant/account permissions are ready.

Current verified evidence now closes several former manual gates:

- production runtime observability is available;
- the current PR #228 release-candidate merge and production deployment are complete;
- Google Explorer production access is confirmed;
- real Google Ads and GA read-only data has been observed;
- Meta legitimate empty-data behavior has been observed;
- the current Stripe test catalog and webhook endpoint have been observed.

Remaining high-value gates are Stripe test Billing Portal plus full E2E, authenticated desktop/mobile QA, and verified legal entity/contact/retention/subprocessor decisions.

Secrets and credentials are never intentionally committed to the repository. External OpenAI/Google/Meta/SMTP/Stripe services still require correct configuration in the active deployment, and every new pilot customer's provider/account authorization remains separate evidence.
