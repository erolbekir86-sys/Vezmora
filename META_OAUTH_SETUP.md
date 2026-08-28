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

Vexmera accepts either the numeric account ID or an `act_...` ID and normalizes it for the Marketing API.

## Production verification

After adding the environment variables, redeploy production and verify:

1. `/health/runtime` returns `meta_oauth_configured: true`.
2. Meta Connect produces an authorization URL.
3. The callback returns successfully and the connector shows as connected.
4. Save a real beta ad account ID.
5. Run a 7-day Meta sync.
6. Confirm campaign rows appear and KPI aggregation is correct.
7. Confirm no write/management permission is requested during private beta.

## Follow-up hardening before wider launch

Before enabling Meta for a larger customer base:

- Exchange short-lived user tokens for long-lived tokens and track expiry.
- Add reconnect/expiry handling.
- Follow Marketing API pagination for accounts that return more than one Insights page.
- Add rate-limit/backoff handling.
- Keep all external write actions behind explicit approvals even after `ads_management` is introduced.
