# Vexmera Google Ads integration status

_Last reviewed: 2026-09-14_

## Verified production status

- Google Ads API access is attached to the Google Cloud project that owns the deployed OAuth client. Developer tokens were retired as an access-control requirement on 2026-09-09 and are not sent by the current read-only integration.
- Google confirmed **Explorer Access** for the Vexmera Cloud project on 2026-09-12. Explorer Access supports production-account requests with a 2,880-operation rolling 24-hour limit, which is sufficient for the current five-company read-only pilot unless usage grows materially.
- A production read-only Google Ads sync has succeeded against the linked real account. The latest verified sync returned campaign-level rows without provider warnings or API errors.
- Google Analytics sync also succeeds with real rows, and the application keeps GA sessions semantically separate from paid-ad clicks at the read boundary.
- The manager-to-client relationship is recorded as accepted and active. Successful production campaign reads provide additional evidence that the active OAuth/account topology can reach the intended account.
- External ad execution remains disabled. This status does not authorize campaign, budget, bid or targeting changes.

## Verified code findings and corrections

- Read-only Ads sync previously required a developer token. The revised code uses OAuth and Cloud-project API access, without sending the retired header.
- Google reconnection preserves saved Analytics property and Ads customer settings while replacing credentials and clearing prior sync status.
- Invalid OAuth client and expired/revoked grants produce safe actionable errors. A rejected refresh does not silently reuse a stale access token.
- Ads diagnostics retain the original safe API response shape needed to distinguish access failures from legitimate empty data without repeating credentials or request secrets.
- Configuration readiness no longer treats a developer token as a prerequisite.
- Connector empty-state handling distinguishes verified zero-row results from provider/authentication failures.

## Required production configuration

| Setting | Expected value / comparison |
| --- | --- |
| `VEZMORA_APP_URL` | `https://vexmera.com` |
| `GOOGLE_REDIRECT_URI` | `https://vexmera.com/api/connectors/google/callback` |
| Google OAuth authorized redirect URI | Exact match to `GOOGLE_REDIRECT_URI`, including scheme, host and path |
| `GOOGLE_CLIENT_ID` | Same Web application OAuth client whose Cloud project holds the approved Ads API access |
| `GOOGLE_CLIENT_SECRET` | Secret belonging to that client, stored privately in Vercel Production |
| `GOOGLE_ADS_API_VERSION` | Supported production version used by the deployment |
| Vexmera Ads customer ID | Configured inside the authorized workspace; do not copy the full identifier into public release evidence |
| `GOOGLE_ADS_LOGIN_CUSTOMER_ID` | Configure only when required by the active manager hierarchy; do not publish the full identifier in release evidence |

## Pilot interpretation

Explorer Access is a valid production access level. For Vexmera's current private-beta behavior, which uses `GoogleAdsService.SearchStream` and other read-oriented reporting calls, **Basic Access is not a blocker for the five-company pilot** as long as the Explorer quota remains sufficient.

Basic Access should be treated as a scaling/feature upgrade rather than as proof that production reporting works. Apply for it when one of these becomes true:

- production usage approaches the Explorer operation limit;
- Vexmera needs functionality restricted at Explorer level;
- commercial rollout requires additional quota headroom.

Google's current flow requires OAuth Brand Verification before upgrading from Explorer to Basic. The legacy Basic application submitted before the 2026-09-09 migration is not an active review path and must not be treated as pending approval.

## Remaining verification before each pilot company

1. Confirm the pilot customer's Google user is authorized for the intended Ads account.
2. Confirm the correct customer/account selection inside Vexmera without placing full identifiers in pilot evidence.
3. Run a fresh read-only sync and record whether it returns real rows or a legitimate verified empty state.
4. Treat authentication, permission and provider failures as errors, never as healthy zero-data states.
5. Keep execution locks enabled throughout the private beta.

See Google's current migration and access-level documentation for the external platform rules. The repo should track observed product behavior and non-secret evidence, not duplicate account credentials or raw account identifiers.
