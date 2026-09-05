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

The preflight verifies active monthly SEK prices and expected amounts without printing the Stripe secret or any Price IDs. A non-zero exit status means billing must remain blocked until the catalog is reconciled.

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
- `VEZMORA_AUTOPILOT_EXECUTION_ENABLED` defaults to disabled.
- Keep both disabled throughout the private beta unless a reviewed production policy explicitly enables them.
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

Important: `stripe_configured` only confirms that the expected environment variables are present. It does not prove that the configured Price IDs exist or match Vexmera's prices. Use `scripts/verify_stripe_catalog.py` for that check.

## Current recommended order

1. Core internal secrets (`VEZMORA_APP_URL`, `VEZMORA_SECRET_KEY`, `CRON_SECRET`).
2. Transactional email.
3. Google/Meta read-only OAuth.
4. Reconcile and verify the Stripe catalog, then run a full test-mode Checkout/webhook/portal flow.
5. Stripe live billing only after pricing, legal pages and canonical domain are final.
6. External ad-account execution only after explicit production approval and connector testing.
