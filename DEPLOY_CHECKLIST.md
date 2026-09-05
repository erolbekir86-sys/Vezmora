# Vexmera 0.6.1 — launch checklist

## Core platform
- [x] Private Beta application built
- [x] 94 automated tests passing on the latest verified CI run
- [x] 14-day Checkout trial implemented
- [x] Customer Portal + signed webhook flow implemented
- [x] Vercel FastAPI entrypoint configured
- [x] Serverless worker fallback implemented
- [x] CRON_SECRET-protected maintenance endpoint implemented
- [x] Persistent Neon/Postgres database provisioned
- [x] PostgreSQL compatibility layer implemented
- [x] Secret scan clean
- [x] GitHub Actions CI included
- [x] Modernize GitHub Actions to checkout/setup-python/setup-node v7 with read-only permissions, concurrency control, timeout and pip caching
- [x] Validate Python plus all shipped frontend JavaScript in CI
- [x] Fix Python packaging and restore green GitHub Actions CI
- [x] Add safe `/health/runtime` deployment diagnostics
- [x] Add safe `/health/beta-readiness` diagnostics without exposing secret values
- [x] Add deployment preflight that fails if private-beta execution flags are accidentally enabled
- [x] Treat development reset-token exposure as an unsafe private-beta configuration
- [x] Reject non-HTTPS app URLs or explicitly insecure cookies in production-like preflight checks
- [x] Verify external execution and Autopilot are blocked by default before external adapters can run
- [x] Add safe production readiness flags for remaining integrations
- [x] Add safe Stripe sandbox readiness diagnostics that compare configured test prices without exposing Price IDs or keys
- [x] Keep the existing GitHub repository connected while rebranding the product to Vexmera
- [x] Keep the existing Vercel project/team connection while rebranding the product to Vexmera

## Production infrastructure
- [x] Add `DATABASE_URL` as a Vercel environment variable
- [x] Correct the production `DATABASE_URL` key spelling and refresh the Neon pooled connection string
- [x] Add `OPENAI_API_KEY` as a Vercel sensitive environment variable
- [x] Route Vercel through root serverless/Postgres bootstrap
- [x] Refresh production secrets and trigger clean redeploy
- [x] Re-enter Neon `DATABASE_URL` from verified project connection string
- [x] Re-enter `OPENAI_API_KEY` through the secure OpenAI Platform flow
- [x] Verify production `/health` endpoint responds
- [x] Verify production app boots with persistent database connection configured
- [x] Verify `/health/runtime` sees `DATABASE_URL` and `OPENAI_API_KEY` in the active production deployment
- [x] Confirm explicit `database_connection_ok` health ping on the latest deployment
- [x] Confirm explicit `openai_connection_ok` production API connectivity
- [x] Diagnose Core/Pulse/Launch production blocker as OpenAI `insufficient_quota` (HTTP 429)
- [x] Activate sufficient OpenAI API billing/quota for the production project
- [x] Run a live OpenAI smoke test through Core/Pulse/Launch
- [x] Remove temporary deep smoke-test code after verification
- [x] Default production session cookies to Secure on Vercel/HTTPS
- [x] Add browser security headers to production responses
- [x] Prevent caching of API and health responses
- [x] Update deployment preflight for Neon/Postgres instead of legacy Turso-only requirements
- [x] Add private-beta safety verification for Stripe, SMTP, Google, Meta and execution-lock configuration
- [x] Verify latest account-privacy backend commit received successful Vercel deployment status
- [x] Trigger clean production redeploy after adding internal Vercel secrets
- [x] Retry production deployment after environment propagation
- [x] Correct production environment whitespace issue and trigger clean redeploy
- [x] Verify `VEZMORA_APP_URL`, `VEZMORA_SECRET_KEY`, and `CRON_SECRET` in production
- [ ] Add remaining Vercel Sensitive Environment Variables as required by final launch configuration

## Billing and email
- [x] 14-day Stripe Checkout trial flow implemented in the application
- [x] Prevent Checkout from resetting or extending an already-running/expired private-beta trial
- [x] Customer Portal and signed webhook handling implemented in the application
- [x] Trigger production redeploy after earlier Stripe sandbox environment setup
- [x] Trigger production redeploy after adding Resend SMTP environment variables
- [x] Trigger production redeploy after correcting `SMTP_HOST`
- [x] Configure and verify Resend SMTP/transactional email sender
- [x] Align Vexmera plan metadata and team limits with Starter 1 / Growth 3 / Scale 10 users
- [x] Verify the currently connected Stripe test account had no usable Vexmera products/prices before reconciliation
- [x] Create fresh Vexmera Starter / Growth / Scale products in the connected Stripe test account
- [x] Create and verify monthly recurring SEK test prices at 1,499 / 2,999 / 5,999 SEK
- [x] Add safe Stripe catalog verification code and unit tests without exposing secrets
- [x] Document the verified test-only catalog in `STRIPE_SANDBOX_CATALOG.md`
- [x] Confirm the currently connected Stripe test account has no webhook endpoint yet
- [x] Add non-secret `/health/beta-readiness` checks for Stripe key mode, exact verified sandbox catalog match and webhook-secret presence
- [ ] Point Vercel `STRIPE_PRICE_STARTER`, `STRIPE_PRICE_GROWTH`, and `STRIPE_PRICE_SCALE` to the newly verified test prices
- [ ] Confirm the Vercel `STRIPE_SECRET_KEY` belongs to the same connected Stripe test account
- [ ] Create/reconcile the active test webhook endpoint at `<VEZMORA_APP_URL>/api/billing/webhook`
- [ ] Confirm `/health/beta-readiness` reports `stripe_sandbox_ready=true` in the configured deployment
- [ ] Run `python scripts/verify_stripe_catalog.py` in the configured deployment environment
- [ ] Run a fresh end-to-end sandbox Checkout + 14-day trial + signed webhook + Customer Portal test
- [ ] Make a separate VAT/tax decision before any live-mode paid launch

## Google
- [x] Trigger production redeploy after adding Google OAuth environment variables
- [x] Configure Google OAuth redirect URL and production environment variables
- [x] End-to-end test Google OAuth with a beta test account
- [x] Enable Google Analytics Data API
- [x] Configure GA4 property and web stream
- [x] Install GA4 tag in production
- [x] Confirm Google Analytics sync returns real rows
- [x] Save Google Ads customer ID `638-343-6270` in Vexmera
- [x] Create Google Ads Manager account for Vexmera (`944-502-2492`)
- [x] Create Google Ads API developer token
- [x] Add `GOOGLE_ADS_DEVELOPER_TOKEN` to Vercel Production and redeploy successfully
- [x] Submit Google Ads API Basic Access application with Vexmera tool documentation
- [x] Send manager-account link request from Vexmera MCC to Google Ads account `638-343-6270`
- [x] Add owner/admin-only Google disconnect endpoint with local credential deletion and best-effort upstream revocation
- [ ] Accept the pending manager-account link request from Google Ads account `638-343-6270`
- [ ] Receive Google approval for Basic Access
- [ ] Configure `GOOGLE_ADS_LOGIN_CUSTOMER_ID` if required after manager linking is active
- [ ] Complete Google Ads sync against a real linked account and confirm campaign-level rows

## Meta
- [x] Add Meta OAuth production runbook and read-only safety tests
- [x] Trigger production redeploy after adding Meta OAuth environment variables
- [x] Configure Meta OAuth redirect URL and production environment variables
- [x] End-to-end test Meta OAuth with a beta test account
- [x] Connect Meta ad account and verify account-level read access
- [x] Confirm read-only Meta sync handles an account with no campaigns correctly
- [x] Add owner/admin-only Meta disconnect endpoint with local credential deletion and best-effort upstream revocation

## Privacy and data controls
- [x] Prevent connector secret blobs from appearing in normal API responses
- [x] Add self-service backend disconnect flow for Google and Meta
- [x] Add customer-facing disconnect controls in the authenticated UI
- [x] Delete local encrypted connector credentials even when provider-side revocation cannot be completed
- [x] Clear saved provider/account identifiers and pending OAuth states on disconnect
- [x] Keep disconnect idempotent and covered by regression tests
- [x] Document that disconnect retains previously synchronized reporting history
- [x] Add an owner/admin-only backend deletion flow for retained synchronized campaign metrics, provider KPIs, anomalies and anomaly notifications
- [x] Require explicit destructive confirmation before synchronized-history deletion
- [x] Preserve manually entered KPI rows during synchronized-history deletion
- [x] Add a customer-facing UI for the separately confirmed synchronized-history deletion flow
- [x] Add guarded self-service account-deletion backend with current-password re-authentication and exact destructive confirmation
- [x] Block account deletion while an owned workspace contains other members or has an active Stripe subscription
- [x] Remove solo-owned workspaces, sessions, memberships, pending invites and queued account email during local account deletion
- [x] Best-effort revoke Google/Meta OAuth tokens for solo-owned workspaces before local account deletion
- [x] Preserve workspaces owned by other users when a departing account is only a member
- [x] Verify account-deletion backend with green CI and successful Vercel deployment status
- [ ] Add the guarded account-deletion control to the authenticated customer UI before marking full self-service deletion complete
- [ ] Finalize concrete production retention periods and subprocessor disclosures

## Product and launch
- [x] Improve Google Ads error diagnostics so sync exposes a safe Google API reason instead of only an HTTP status
- [x] Align public marketing and Command Center branding, pricing and private-beta language
- [x] Complete the current AI Command Center customer-facing polish pass
- [x] Finish the Swedish dynamic-copy polish for the authenticated app
- [x] Verify connector-disconnect UI with green CI and successful Vercel deployment status
- [x] Verify synchronized-history deletion backend and UI with green CI and successful Vercel deployment status
- [x] Raise automated coverage to 94 passing tests across deployment, billing, privacy, integrations, UI and execution safety
- [ ] Perform final authenticated browser QA on the deployed Command Center
- [ ] Finalize Privacy Policy and Beta Terms with legal entity/contact details and legal review before external pilot onboarding
- [ ] Purchase/attach `vexmera.com` when the product is production-ready
- [ ] Run five-company pilot
