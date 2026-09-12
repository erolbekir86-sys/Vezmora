# Vexmera Google Ads integration status

_Last reviewed: 2026-09-12_

## Verified code findings and corrections

- Production at the start of this audit used `main` revision `c63919d`.
- Read-only Ads sync incorrectly required a developer token. The revised code uses OAuth and Cloud-project API access, without sending the retired header.
- Google reconnection erased saved Analytics property and Ads customer IDs. The callback now preserves those settings while replacing credentials and clearing prior sync status.
- Invalid OAuth client and expired/revoked grants now produce safe actionable errors. A rejected refresh no longer silently reuses a stale access token.
- Ads diagnostics now retain the original API response, including array-shaped searchStream errors and request IDs. They identify Cloud-project production access failures without repeating the failed request.
- Configuration readiness no longer treats a developer token as a prerequisite. Live account access remains a separate verification gate.

## Required production configuration

| Setting | Expected value / comparison |
| --- | --- |
| `VEZMORA_APP_URL` | `https://vexmera.com` |
| `GOOGLE_REDIRECT_URI` | `https://vexmera.com/api/connectors/google/callback` |
| Google OAuth authorized redirect URI | Exact match to `GOOGLE_REDIRECT_URI`, including scheme, host, path and trailing slash |
| `GOOGLE_CLIENT_ID` | Same Web application OAuth client selected in Google Cloud |
| `GOOGLE_CLIENT_SECRET` | Secret belonging to that client, stored privately in Vercel Production |
| `GOOGLE_ADS_API_VERSION` | `v25` |
| Vexmera Ads customer ID | Historical target `6383436270`; confirm intended account |
| `GOOGLE_ADS_LOGIN_CUSTOMER_ID` | `9445022492` if using the historical MCC access path; otherwise verify topology before setting |

## External verification still required

1. Identify the Cloud project owning the deployed OAuth client; confirm Ads API is enabled and the project has production access.
2. Verify the OAuth audience/publishing state, applicable test users, requested scopes and exact callback registration.
3. Compare Vercel Production client ID, secret and callback with that Cloud client. Redeploy after any environment change.
4. Confirm the authorized Google user can access the intended Ads account and, where required, the active MCC/client link. The deployment checklist records the historical link as accepted on 2026-09-05; this audit has not independently rechecked it.
5. Reconnect Google in Vexmera, save/confirm source IDs, and run a read-only sync. Confirm actual campaign rows or a successful empty response with no API error. Confirm Analytics continues to work.

The Cloud Console was unavailable in the audit browser. Vercel environment settings and Vexmera's authenticated application require sign-in. No claim of current Cloud configuration, access approval, live environment-value parity or end-to-end production sync is made from code tests alone.

## Google access migration

Google moved Ads API access to Cloud projects on 2026-09-09. Pending old Basic Access applications were closed and must be reconsidered through Cloud Console; do not rely on the historical 2026-09-03 API Center application as proof of current status. See [Google's migration guide](https://developers.google.com/google-ads/api/docs/api-policy/developer-token) and [access levels](https://developers.google.com/google-ads/api/docs/api-policy/access-levels).

The beta integration remains read-only; this work does not enable changes to campaigns, budgets, bids or targeting.
