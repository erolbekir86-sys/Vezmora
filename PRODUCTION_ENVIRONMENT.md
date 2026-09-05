# Vexmera production environment runbook

This file documents environment variable names only. Never commit real secrets or credentials to GitHub.

## Core production runtime

Required:

- `DATABASE_URL` — Neon pooled PostgreSQL connection string.
- `OPENAI_API_KEY` — OpenAI project API key.
- `VEZMORA_APP_URL` — canonical HTTPS app URL, without a trailing slash.
- `VEZMORA_SECRET_KEY` — long random secret used to encrypt OAuth connector tokens at rest.
- `CRON_SECRET` — long random secret required by the internal maintenance endpoint.

Optional/defaulted by the Vercel bootstrap:

- `OPENAI_MODEL` — defaults to the production model configured in `main.py` when empty.
- `VEZMORA_COOKIE_SECURE` — normally omit on Vercel; HTTPS deployments default to secure cookies.
- `VEZMORA_SERVERLESS` — forced on by the Vercel bootstrap.

## Stripe billing

Required before enabling production billing:

- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_STARTER`
- `STRIPE_PRICE_GROWTH`
- `STRIPE_PRICE_SCALE`

The three Price IDs must exist in the same Stripe account and mode as `STRIPE_SECRET_KEY` and must be monthly recurring SEK prices with these exact unit amounts before VAT:

- Starter: `149900` öre = 1,499 SEK/month
- Growth: `299900` öre = 2,999 SEK/month
- Scale: `599900` öre = 5,999 SEK/month

Optional:

- `VEZMORA_TRIAL_DAYS` — defaults to `14`.

Production webhook route:

- `<VEZMORA_APP_URL>/api/billing/webhook`

Expected event types:

- `checkout.session.completed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_failed`

Do not mix Stripe test-mode IDs/keys with live-mode IDs/keys. Never assume a historical Price ID is still valid in the active Stripe account.

Before enabling paid Checkout, run:

```bash
python scripts/verify_stripe_catalog.py
```

The catalog verifier checks active monthly SEK prices and expected amounts without printing the Stripe secret or any Price IDs. A non-zero exit status means billing must remain blocked until the catalog is reconciled.

## Transactional email

Minimum required:

- `SMTP_HOST`
- `SMTP_FROM`

Usually required by the provider:

- `SMTP_PORT` — defaults to `587`.
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_STARTTLS` — defaults to `true`.

## Google Analytics + Google Ads

OAuth connection requires:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`

Google Ads data additionally requires:

- `GOOGLE_ADS_DEVELOPER_TOKEN`

Optional:

- `GOOGLE_ADS_LOGIN_CUSTOMER_ID`
- `GOOGLE_ADS_API_VERSION`

The redirect URI must exactly match the callback URL registered in Google Cloud.

A configured developer token does not prove that Google has granted the required API access level or that the Ads account is linked to the manager account. Treat Basic Access approval and manager linking as separate external checks.

## Meta Ads

OAuth connection requires:

- `META_APP_ID`
- `META_APP_SECRET`
- `META_REDIRECT_URI`

Optional:

- `META_GRAPH_VERSION`
- `VEZMORA_ENABLE_META_EXECUTION_SCOPE` — must remain disabled for the read-only private beta.

The redirect URI must exactly match the valid OAuth redirect URI registered in the Meta app.

## External execution safety

The private beta is intentionally read-only for external advertising mutations.

These flags must remain disabled:

- `VEZMORA_EXECUTION_ENABLED=false`
- `VEZMORA_AUTOPILOT_EXECUTION_ENABLED=false`
- `VEZMORA_ENABLE_META_EXECUTION_SCOPE=false`

Vexmera may prepare recommendations and Queue items for human review while these locks remain off. Direct execution tests verify that the external Google/Meta adapter is not reached when the master execution flag is disabled, and Autopilot remains disabled unless both execution gates are deliberately enabled.

Do not enable any of these flags merely because OAuth is working. External execution requires a separate production review of permissions, approval gates, account-level testing and rollback behavior.

## Safe deployment preflight

Run the deployment preflight in the same environment that will serve Vexmera:

```bash
python scripts/preflight.py
```

For machine-readable output that is safe to archive in CI logs:

```bash
python scripts/preflight.py --json
```

The preflight reports only configuration names, booleans and missing-variable names. It never prints environment values. It checks:

- core application secrets and persistent database configuration
- Stripe billing variable presence
- transactional email minimum configuration
- Google OAuth and Google Ads developer-token presence
- Meta OAuth configuration
- serverless mode
- private-beta execution locks

During the private beta the command intentionally exits non-zero if a core requirement is missing **or if any private-beta execution flag is accidentally enabled**.

## Safe runtime diagnostics

After any environment change, redeploy Vercel and inspect:

- `/health/runtime`
- `/health/beta-readiness`

`/health/runtime` exposes non-secret infrastructure booleans such as:

- `database_connection_ok`
- `openai_connection_ok`
- `internal_secrets_configured`
- `stripe_configured`
- `smtp_configured`
- `google_oauth_configured`
- `meta_oauth_configured`

`/health/beta-readiness` exposes private-beta safety/readiness booleans including:

- whether external execution is enabled
- whether Autopilot execution is enabled
- whether Meta execution scope is enabled
- whether the private-beta execution posture is safe
- whether Stripe catalog/webhook variables are present
- whether Google/Meta OAuth and SMTP minimum configuration are present
- which privacy controls are implemented

Both endpoints are designed not to expose secret values.

Important limitations:

- configuration booleans do not prove third-party approval, account access, webhook delivery or end-to-end behavior;
- `stripe_configured` only confirms that expected environment variables are present;
- Google Ads Basic Access and manager-account linking require separate verification;
- use `scripts/verify_stripe_catalog.py` for the Stripe catalog and run an actual test-mode Checkout/webhook/Portal flow before paid launch.

## Privacy controls in the private beta

The authenticated Connect view now separates two different operations:

1. **Disconnect Google/Meta** — removes locally stored connector credentials, clears connector/account identifiers, stops future sync access and attempts provider-side revocation where supported. Previously synchronized reporting history remains.
2. **Delete synchronized marketing history** — a separate owner/admin-only destructive action with typed confirmation. It removes synchronized campaign metrics, Google/Meta/Analytics KPI rows and related anomaly records while preserving manually entered KPI rows and connector credentials.

Neither operation is a complete account deletion or complete personal-data erasure process. Full account deletion, final retention periods and formal data-rights procedures remain launch work.

## Current recommended order

1. Core internal secrets (`VEZMORA_APP_URL`, `VEZMORA_SECRET_KEY`, `CRON_SECRET`).
2. Persistent database and OpenAI connectivity.
3. Transactional email.
4. Google/Meta read-only OAuth.
5. Run `scripts/preflight.py` and confirm private-beta execution locks are SAFE.
6. Reconcile and verify the Stripe test catalog, then run a full test-mode Checkout/webhook/Portal flow.
7. Complete authenticated browser QA including connector disconnect and synchronized-history deletion controls.
8. Finalize legal entity details, privacy/terms, retention/subprocessor disclosures, VAT/tax treatment and canonical domain.
9. Stripe live billing only after the preceding launch blockers are resolved.
10. External ad-account execution only in a later, explicitly reviewed production phase.
