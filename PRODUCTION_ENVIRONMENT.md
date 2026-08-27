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

Do not mix Stripe test-mode IDs/keys with live-mode IDs/keys.

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

## Meta Ads

OAuth connection requires:

- `META_APP_ID`
- `META_APP_SECRET`
- `META_REDIRECT_URI`

Optional:

- `META_GRAPH_VERSION`
- `VEZMORA_ENABLE_META_EXECUTION_SCOPE` — leave disabled for read-only beta use.

The redirect URI must exactly match the valid OAuth redirect URI registered in the Meta app.

## External execution safety

- `VEZMORA_EXECUTION_ENABLED` defaults to disabled.
- Keep it disabled until Google/Meta connections, approval gates and real-account previews have been verified.
- Vexmera should continue to prepare actions for human approval while execution remains disabled.

## Safe verification

After any environment change, redeploy Vercel and inspect `/health/runtime`.

The endpoint exposes booleans only for configuration/readiness and never returns secret values. Relevant flags include:

- `database_connection_ok`
- `openai_connection_ok`
- `internal_secrets_configured`
- `stripe_configured`
- `smtp_configured`
- `google_oauth_configured`
- `meta_oauth_configured`

## Current recommended order

1. Core internal secrets (`VEZMORA_APP_URL`, `VEZMORA_SECRET_KEY`, `CRON_SECRET`).
2. Transactional email.
3. Google/Meta read-only OAuth.
4. Stripe production billing after pricing/domain decisions are final.
5. External ad-account execution only after explicit production approval and connector testing.
