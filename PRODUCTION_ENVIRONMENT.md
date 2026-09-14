# Vexmera production environment runbook

This file documents production configuration names and non-secret validation rules only. Never commit real secrets, OAuth credentials, Stripe identifiers, full advertising-account identifiers or database connection strings to GitHub.

## Core production runtime

Required:

- `DATABASE_URL` — Neon pooled PostgreSQL connection string.
- `OPENAI_API_KEY` — OpenAI project API key.
- `VEZMORA_APP_URL` — canonical HTTPS app URL, without a trailing slash.
- `VEZMORA_SECRET_KEY` — long random secret used to encrypt OAuth connector tokens at rest.
- `CRON_SECRET` — long random secret required by the internal maintenance endpoint.

Optional/defaulted by the Vercel bootstrap:

- `OPENAI_MODEL` — defaults to the production model configured in code when empty.
- `VEZMORA_COOKIE_SECURE` — normally omit on Vercel; HTTPS deployments force secure cookies.
- `VEZMORA_SERVERLESS` — forced on by the Vercel bootstrap.

## Stripe billing

Required for the current private-beta **sandbox** billing verification:

- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_START`
- `STRIPE_PRICE_GROWTH`
- `STRIPE_PRICE_PRO`
- `VEZMORA_STRIPE_PRICING_VERSION`

The three configured Price IDs must belong to the same Stripe **test-mode** account as `STRIPE_SECRET_KEY` and must be active monthly recurring SEK prices with these exact unit amounts before VAT:

- Start: `99500` öre = 995 SEK/month
- Growth: `149500` öre = 1,495 SEK/month
- Pro: `299500` öre = 2,995 SEK/month

The accepted pricing-version marker is:

- `2026-09-start-growth-pro`

Do not set or treat that marker as approval until the deployed sandbox catalog has been verified.

Optional:

- `VEZMORA_TRIAL_DAYS` — defaults to `14`.

Sandbox webhook route:

- `<VEZMORA_APP_URL>/api/billing/webhook`

Expected event types:

- `checkout.session.completed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_failed`

Do not mix Stripe test-mode IDs/keys with live-mode IDs/keys. Never reuse the historical Starter/Growth/Scale Price IDs for the current Start/Growth/Pro model.

Before opening private-beta Checkout, run in the configured deployment environment:

```bash
python scripts/verify_stripe_catalog.py
```

The read-only verifier requires:

- configured Price identity matches the retrieved Price;
- `active=true`;
- `livemode=false`;
- currency `sek`;
- recurring monthly type;
- exact amount 995 / 1,495 / 2,995 SEK;
- explicit current pricing-version metadata/marker alignment.

The verifier must never print Stripe secrets, configured Price IDs, Product IDs, raw Stripe payloads or raw Stripe exceptions. A non-zero exit status means Checkout stays blocked.

A **test-mode Billing Portal configuration** is a separate E2E requirement. Its customer-facing cancellation, plan-change and payment-method policy is an owner/business decision and must not be invented by automation. Live-mode paid billing, VAT/tax, bank details and KYC are separate future launch decisions.

## Transactional email

Minimum required:

- `SMTP_HOST`
- `SMTP_FROM`

Usually required by the provider:

- `SMTP_PORT` — defaults to `587` and must be a valid TCP port.
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_STARTTLS` — defaults to `true`.

For Vercel private beta, `SMTP_STARTTLS` must remain enabled. The application fails closed before connecting if it is explicitly disabled, and operator preflight marks production transport unsafe.

## Google Analytics + Google Ads

OAuth connection requires:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`

Google Ads reporting additionally requires a customer ID stored in the workspace and Ads API access on the Google Cloud project owning `GOOGLE_CLIENT_ID`. Since 2026-09-09, the read-only integration does not require or send `GOOGLE_ADS_DEVELOPER_TOKEN`.

Optional:

- `GOOGLE_ADS_LOGIN_CUSTOMER_ID` — set only if the active manager hierarchy requires it.
- `GOOGLE_ADS_API_VERSION` — use a supported production version.

The production callback relationship must be exact:

```text
VEZMORA_APP_URL=https://vexmera.com
GOOGLE_REDIRECT_URI=https://vexmera.com/api/connectors/google/callback
```

The registered Google OAuth Web application must use that callback and correspond to the same Cloud project whose Google Ads API access was approved. Keep the client secret private in Vercel.

### Current verified access posture

- Google approved **Explorer Access** for the Vexmera Cloud project on 2026-09-12.
- Explorer is a production access level and currently supports the read-only reporting pattern used by Vexmera.
- A real production Google Ads read-only sync has successfully returned campaign-level rows without provider warnings.
- The manager/client relationship is recorded as accepted and active.

Basic Access is therefore **not a current five-company read-only pilot blocker**. It becomes a future upgrade when Explorer quota or feature restrictions are insufficient. Google's current upgrade flow requires OAuth Brand Verification followed by the Cloud Console access-upgrade flow. The legacy pre-migration Basic application must not be treated as pending review.

Do not place full customer IDs, manager IDs, OAuth client IDs, access tokens or request credentials in release evidence, logs, PRs or public documentation.

The customer-facing Google Analytics tag is separate from connector APIs. In the authenticated application, analytics storage defaults to denied, the tag loads only after explicit opt-in, and Google Signals/ad-personalization remain disabled.

## Meta Ads

OAuth connection requires:

- `META_APP_ID`
- `META_APP_SECRET`
- `META_REDIRECT_URI`

Optional:

- `META_GRAPH_VERSION`
- `VEZMORA_ENABLE_META_EXECUTION_SCOPE` — must remain disabled for read-only private beta.

The redirect URI must exactly match the valid OAuth redirect URI registered in the Meta app. Provider/authentication failure must not be converted into healthy zero data.

## External execution safety

The private beta is intentionally read-only for external advertising mutations.

These flags must remain disabled:

- `VEZMORA_EXECUTION_ENABLED=false`
- `VEZMORA_AUTOPILOT_EXECUTION_ENABLED=false`
- `VEZMORA_ENABLE_META_EXECUTION_SCOPE=false`

Vexmera may prepare recommendations and Queue items for human review while these locks remain off. Do not enable any execution flag merely because OAuth/reporting works.

## Safe deployment preflight

Run in the same environment serving Vexmera:

```bash
python scripts/preflight.py
```

Machine-readable form:

```bash
python scripts/preflight.py --json
```

The preflight reports configuration names, booleans and missing-variable names rather than secret values. During private beta it must fail closed when a core requirement is missing, an execution flag is unexpectedly enabled or production transport is unsafe.

For the Stripe catalog use:

```bash
python scripts/verify_stripe_catalog.py
```

## Safe runtime diagnostics

After any deployment change inspect:

- `/health/runtime`
- `/health/beta-readiness`

Production `/health/runtime` is intentionally minimal and should expose only liveness/deployment identity fields needed to prove which build is serving traffic. It must not expose database, OpenAI, Stripe, SMTP, OAuth or secret-configuration booleans.

Production `/health/beta-readiness` exposes only the small private-beta safety surface needed to verify that external execution is still locked and transport is safe.

For configuration evidence that must remain non-secret, run `scripts/preflight.py` in the configured deployment environment. Public health endpoints are deliberately not a replacement for operator preflight.

Latest direct runtime inspection verified production observability and the intended production revision for the current baseline. Re-run these checks after the next merged release.

Important limitations:

- health/safety booleans do not prove provider authorization, billing E2E or authenticated browser behavior;
- Google Explorer Access and real read-only sync are already verified for the current pilot baseline, but each pilot customer's authorization still needs a fresh read-only check;
- use `scripts/verify_stripe_catalog.py` plus an actual test-mode Checkout/webhook/Customer Portal flow before billing-enabled pilot onboarding;
- authenticated desktop/mobile QA remains a separate launch gate.

## Privacy controls in the private beta

The authenticated application separates these operations:

1. **Disconnect Google/Meta** — removes locally stored connector credentials, clears connector/account identifiers, stops future sync and attempts provider-side revocation where supported. Previously synchronized reporting history remains.
2. **Delete synchronized marketing history** — owner/admin destructive action with explicit confirmation. It removes synchronized campaign metrics, provider KPI rows and related anomaly data while preserving manually entered KPI rows and connector credentials.
3. **Delete Vexmera account** — guarded full-account flow with blocker preview, current-password re-authentication and exact confirmation. It does not promise deletion of processor-held billing/compliance records that may be legally required.
4. **Analytics consent** — optional analytics storage defaults to denied; settings can be reopened and first-party analytics cookies are best-effort cleared when consent is withdrawn.

Technically verified short-lived capability retention:

- authenticated sessions: 14 days;
- password reset links: 60 minutes;
- workspace invites: 7 days;
- expired/superseded capability rows are pruned by the application retention guards.

The current Neon project history-retention setting is 6 hours. Treat that as observed infrastructure evidence, not as a universal public backup-retention promise. Longer-lived product data, provider logs, AI history, billing/compliance records and processor disclosures still require owner/legal review.

## Current recommended order

1. Keep core secrets, database, OpenAI and transactional email healthy without exposing values.
2. Keep Google/Meta read-only OAuth and external-execution locks unchanged.
3. Get the current PR through fresh green CI, merge and confirm the deployed revision.
4. Reconcile deployed Stripe sandbox variables, configure the test Billing Portal after owner policy selection, and run full Checkout/trial/webhook/Portal E2E.
5. Complete authenticated desktop and mobile browser QA.
6. Finalize legal entity/contact details, longer-lived retention/subprocessor disclosures and Privacy/Terms review.
7. Decide VAT/tax and live billing separately.
8. Consider Google Basic Access only when Explorer quota/functionality is insufficient.
9. External ad-account execution remains a later explicitly reviewed production phase.
