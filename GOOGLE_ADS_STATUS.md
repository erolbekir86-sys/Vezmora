# Vexmera Google Ads integration status

_Last updated: 2026-09-03_

## Current state

- Google OAuth is connected in production.
- Google Analytics Data API is enabled and Vexmera has successfully synced real Analytics rows.
- Google Ads Customer ID configured in Vexmera: `638-343-6270`.
- Vexmera Google Ads Manager (MCC): `944-502-2492`.
- Google Ads developer token has been created and stored as a Vercel production environment variable.
- Developer token currently has **Test Account Access**.
- **Basic Access application submitted to Google on 2026-09-03.**
- A manager-to-client account linking request has been sent from MCC `944-502-2492` to client account `638-343-6270`.
- Current Google Ads sync reaches the API path but returns HTTP `404`.

## What Vexmera currently does

The beta integration is read-only. It retrieves campaign-level performance data for reporting and AI-assisted analysis. It does not create or modify campaigns, ads, budgets, bids, targeting, or account settings.

Current requested performance fields include:

- date
- account currency
- campaign ID and name
- impressions
- clicks
- conversions
- conversion value
- cost

## Remaining external blockers

1. The client account must accept the pending manager-link request.
2. Google must approve the Basic Access application before the developer token can be used against normal production accounts.
3. The client Google Ads account must be fully enabled/configured enough for API access.

## Production configuration to verify after linking

When the MCC/client hierarchy is active, verify that production uses:

```text
GOOGLE_ADS_LOGIN_CUSTOMER_ID=9445022492
```

The client/customer ID used for data retrieval remains:

```text
6383436270
```

## Next test

After the manager link is accepted and Basic Access is approved:

1. Re-run Google sync from Vexmera Connect.
2. Confirm Analytics still syncs normally.
3. Confirm Google Ads returns campaign data, or a valid empty result when no campaigns/data exist.
4. If Google Ads still fails, record only safe API diagnostic information such as HTTP status, Google Ads error code/message, and request ID. Never expose OAuth access tokens, refresh tokens, developer token, or client secrets.

## Definition of done

Google Ads integration is considered beta-ready when an authorized production account can complete a read-only sync end-to-end without exposing secrets, and empty/no-campaign accounts are handled cleanly.
