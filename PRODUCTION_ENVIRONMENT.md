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

`VEZMORA_STRIPE_PRICING_VERSION` must remain blank until the current sandbox catalog has been independently verified. After verification, the only accepted marker for this pricing model is:

- `2026-09-start-growth-pro`

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

The canonical catalog verifier is read-only. It retrieves only the three configured Price objects and verifies:

- configured Price ID matches the returned Price;
- `active=true`;
- `livemode=false`;
- currency is `sek`;
- Price type is recurring;
- interval is one month;
- amount exactly matches 995 / 1,495 / 2,995 SEK;
- the explicit current pricing-version marker matches.

The verifier never prints the Stripe secret, configured Price IDs, Product IDs, raw Stripe payloads or raw Stripe exceptions. A non-zero exit status means Checkout must remain blocked until the sandbox catalog and marker are reconciled.

Live-mode paid billing is a separate future launch decision. The private-beta sandbox verifier intentionally rejects live-mode Price objects.

## Transactional email

Minimum required:

- `SMTP_HOST`
- `SMTP_FROM`

Usually required by the provider:

- `SMTP_PORT` — defaults to `587` and must be a valid TCP port.
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_STARTTLS` — defaults to `true`.

For the supported Vercel private-beta runtime, `SMTP_STARTTLS` must remain enabled. The application fails closed before connecting if it is explicitly disabled, and `scripts/preflight.py` marks production transport unsafe. This prevents password-reset and workspace-invite capability links, as well as SMTP credentials, from being sent over an accidentally plaintext SMTP connection.

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

The customer-facing Google Analytics tag is separate from the connector API. In the authenticated web application, analytics storage defaults to denied and the Google Analytics script is loaded only after explicit opt-in consent. Google Signals and ad-personalization signals remain disabled.

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
- transactional email minimum configuration and production STARTTLS safety
- Google OAuth and Google Ads developer-token presence
- Meta OAuth configuration
- serverless mode
- private-beta execution locks

During the private beta the command intentionally exits non-zero if a core requirement is missing, if a private-beta execution flag is accidentally enabled, or if a production transport guard is unsafe.

## Safe runtime diagnostics

After any environment change, redeploy Vercel and inspect:

- `/health/runtime`
- `/health/beta-readiness`

In production, `/health/runtime` is intentionally minimal. It exposes only liveness/deployment identity fields needed to prove which build is serving traffic, such as service/version, platform/environment and deployment revision. It must not expose database, OpenAI, Stripe, SMTP, OAuth, token or secret-configuration booleans.

In production, `/health/beta-readiness` exposes only the small private-beta safety surface required by public preflight, including whether external execution, Autopilot execution and Meta execution scope are disabled as intended. Fuller configuration diagnostics remain an operator/local concern rather than a public HTTP contract.

Use `python scripts/preflight.py` in the configured deployment environment for database, Stripe, email, Google and Meta configuration checks. Use `python scripts/verify_stripe_catalog.py` for the current Stripe sandbox catalog. Neither public health endpoint should be treated as proof of third-party approval, account access, webhook delivery, billing correctness or end-to-end behavior.

Important limitations:

- liveness and safety booleans do not prove third-party approval, account access, webhook delivery or end-to-end behavior;
- Google Ads Basic Access and manager-account linking require separate verification;
- use `scripts/verify_stripe_catalog.py` for the Stripe sandbox catalog and run an actual test-mode Checkout/webhook/Portal flow before paid launch;
- use controlled real-account read-only syncs to prove Google/Meta integration behavior after external access is available.

## Privacy controls in the private beta

The authenticated application separates several distinct privacy operations:

1. **Disconnect Google/Meta** — removes locally stored connector credentials, clears connector/account identifiers, stops future sync access and attempts provider-side revocation where supported. Previously synchronized reporting history remains.
2. **Delete synchronized marketing history** — a separate owner/admin-only destructive action with typed confirmation. It removes synchronized campaign metrics, Google/Meta/Analytics KPI rows and related anomaly records while preserving manually entered KPI rows and connector credentials.
3. **Delete Vexmera account** — a guarded full account-deletion flow that first previews blockers, requires current-password re-authentication and the exact confirmation phrase `DELETE MY ACCOUNT`, blocks deletion while an owned workspace has other members or an active Stripe subscription, best-effort revokes Google/Meta tokens for solo-owned workspaces, deletes the local account and solo-owned workspace data, and removes memberships from workspaces owned by other users.
4. **Analytics consent** — optional Google Analytics storage defaults to denied. The tag is loaded only after opt-in, settings can be reopened later, and first-party `_ga` cookies are best-effort cleared when consent is denied or withdrawn.

Account deletion does not promise deletion of third-party billing/compliance records that processors may need to retain for accounting, disputes, fraud prevention, security or legal obligations. Final retention periods, processor disclosures and formal public privacy wording still require legal review before external pilot onboarding.

## Current recommended order

1. Core internal secrets (`VEZMORA_APP_URL`, `VEZMORA_SECRET_KEY`, `CRON_SECRET`).
2. Persistent database and OpenAI connectivity.
3. Transactional email with STARTTLS enforced.
4. Google/Meta read-only OAuth.
5. Run `scripts/preflight.py` and confirm private-beta execution locks and production transport are SAFE.
6. Reconcile and verify the current Start/Growth/Pro Stripe test catalog with `scripts/verify_stripe_catalog.py`, then run a full test-mode Checkout/webhook/Portal flow.
7. Complete authenticated browser QA including connector disconnect, synchronized-history deletion, account deletion and analytics-consent controls.
8. Finalize legal entity details, privacy/terms, retention/subprocessor disclosures, VAT/tax treatment and canonical domain.
9. Stripe live billing only after the preceding launch blockers are resolved.
10. External ad-account execution only in a later, explicitly reviewed production phase.
