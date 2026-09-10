# Vexmera Meta OAuth production setup

This runbook covers the production setup for connecting Meta Ads to Vexmera.

## Safety posture

Vexmera is read-only for Meta during the private beta.

- Default OAuth scope: `ads_read`
- Do not enable `ads_management` in production beta.
- Keep `VEZMORA_ENABLE_META_EXECUTION_SCOPE` unset/false.
- Keep `VEZMORA_EXECUTION_ENABLED` disabled until explicit production approval and real-account tests are complete.
- Never commit Meta App Secret, access tokens, or other credentials to GitHub.

## Required Meta app configuration

Create/configure the Meta developer app used by Vexmera and register the production OAuth callback URL exactly as:

`<VEZMORA_APP_URL>/api/connectors/meta/callback`

The scheme, host, path, and trailing slash behavior must match `META_REDIRECT_URI` exactly.

For the private beta, request only the permissions needed to read advertising insights.

## Required production environment variables

Add these as sensitive production environment variables in Vercel:

- `META_APP_ID`
- `META_APP_SECRET`
- `META_REDIRECT_URI`

Optional:

- `META_GRAPH_VERSION` — keep pinned to a supported version after verification.
- `VEZMORA_ENABLE_META_EXECUTION_SCOPE` — leave disabled for private beta.

`VEZMORA_SECRET_KEY` must already be configured because Vexmera encrypts connector tokens before storing them.

## Vexmera OAuth flow

1. An authenticated workspace owner/admin calls `GET /api/connectors/meta/start?workspace_id=<id>`.
2. Vexmera stores a one-time OAuth state and returns the Meta authorization URL.
3. Meta redirects to `/api/connectors/meta/callback` with `code` and `state`.
4. Vexmera validates and consumes the state.
5. Vexmera exchanges the authorization code for an access token.
6. The token payload is encrypted before persistence.
7. The user is redirected to `/?connected=meta`.

## Ad account setup

After OAuth is connected, save the Meta ad account ID in connector settings as `meta_ad_account_id`.

Vexmera accepts either the numeric account ID or an `act_...` ID and normalizes it for the Marketing API. When no valid account ID is stored, the production adapter can discover authorized ad accounts and auto-select the account only when exactly one safe candidate is available.

## Current read-only hardening

The private-beta connector already includes:

- bounded retry for transient Meta API failures such as rate limiting and 5xx responses;
- bounded Insights pagination with loop and page-limit protection;
- campaign/date deduplication before KPI persistence;
- safe reconnect guidance for invalid or expired authorization;
- fail-closed handling for malformed provider responses;
- customer-facing distinction between a healthy empty account and a provider/API failure.

These controls do not enable any Meta write or campaign-management capability.

## Production verification

After adding the environment variables, redeploy production and verify:

1. Run `python scripts/preflight.py` in the configured deployment environment and confirm the Meta OAuth configuration check passes without printing secret values.
2. Confirm public `/health/runtime` returns only minimal liveness/deployment identity and does not expose OAuth, token, Stripe, SMTP or database configuration booleans.
3. Meta Connect produces an authorization URL.
4. The callback returns successfully and the connector shows as connected.
5. Save or safely discover a real beta ad account ID.
6. Run a 7-day Meta read-only sync.
7. Confirm campaign rows appear when the account has data and KPI aggregation is correct.
8. Confirm empty-data and provider-error states remain distinct.
9. Confirm no write/management permission is requested during private beta.

## Follow-up before wider launch

Before enabling Meta for a larger customer base:

- verify long-lived token lifecycle and expiry behavior with real accounts;
- expand ad-account discovery pagination if production accounts exceed the current bounded discovery window;
- monitor Meta Graph API version migration requirements;
- preserve bounded retry/pagination and secret-safe diagnostics as provider behavior changes;
- keep every external write action disabled until a separate, explicit production review authorizes a later execution phase.
