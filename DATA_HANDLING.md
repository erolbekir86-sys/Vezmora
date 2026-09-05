# Vexmera data handling — private beta

This document describes the current implementation as of the private beta codebase. It is operational documentation, not legal advice.

## Connected account data Vexmera stores

For Google and Meta connectors, Vexmera stores a connector record scoped to the customer's workspace. The record contains provider, connection status, optional external/account labels, connector metadata, an encrypted secret blob, and timestamps.

The encrypted secret blob is used to store OAuth token material needed for connected API access. Normal connector reads do not include the secret blob; code paths must explicitly request `include_secret=True` when a backend operation needs credentials.

Connector metadata may include identifiers and operational state such as Google Analytics property ID, Google Ads customer ID, Meta ad account ID, granted scope information, connection time, and last-sync metadata.

## Performance data Vexmera stores

When a sync succeeds, Vexmera can persist campaign-level performance rows including:

- provider
- external campaign ID
- campaign name
- metric date
- impressions
- clicks
- conversions
- spend
- revenue/conversion value
- currency

Vexmera also stores normalized workspace KPI rows used by dashboards and AI context. Currency conversion may be applied to aggregate KPI data using workspace FX settings while raw campaign rows retain source currency values.

## Google data read by the current beta

The current Google connector is read-oriented. Depending on configuration and account access, it can read:

- Google Analytics reporting data for configured properties
- Google Ads campaign performance data for configured customer accounts

The private beta must keep external execution disabled. No campaign creation, publishing, bid changes, budget changes, or autonomous ad mutations are required for the beta data-sync path.

## Meta data read by the current beta

The default Meta OAuth scope is `ads_read`. The private beta must not request `ads_management` unless a later production phase explicitly enables and reviews execution scope.

The current beta sync path is intended to read advertising insights and campaign performance data, not modify campaigns.

## Secrets and user-visible APIs

OAuth tokens, developer tokens, API keys, app secrets, and encrypted connector secret blobs must never be returned in user-visible connector responses, diagnostics, notifications, or normal logs.

Google Ads diagnostics intentionally extract only safe error metadata such as API status, human-readable message, Google Ads error code, and request ID. They must not expose authorization headers, OAuth tokens, developer tokens, or raw secret blobs.

## Disconnect and credential deletion

A self-service disconnect flow is implemented for Google and Meta at `POST /api/connectors/{provider}/disconnect`, with a corresponding control in the authenticated Connect view.

The flow:

1. requires an authenticated workspace owner or admin;
2. performs a best-effort provider-side revocation where supported;
3. removes the locally stored encrypted connector credential even if upstream revocation is unavailable or fails;
4. clears saved external/account identifiers and connector configuration metadata;
5. marks the connector as disconnected;
6. removes outstanding OAuth states for that workspace/provider;
7. returns only safe status booleans and never exposes credentials or provider secrets;
8. is covered by regression tests, including secret-removal and idempotency checks.

Provider-side revocation is intentionally best-effort. A temporary provider/network failure must not prevent Vexmera from deleting its own local credential copy.

### Historical data after disconnect

Disconnecting an account **does not delete previously synchronized KPI or campaign-performance history**. This is deliberate so that a user does not accidentally erase reporting history merely by rotating or reconnecting an OAuth account.

The connector record is reduced to a disconnected state with a timestamp and a marker that historical data is retained. Previously saved property IDs, ad-account IDs and similar connector configuration values are removed from that record.

Customer-facing text distinguishes clearly between:

- **Disconnect account:** remove stored connector credentials and stop future sync access.
- **Delete synchronized history:** separately delete retained provider-synchronized reporting history after explicit destructive confirmation.

## Synchronized reporting-history deletion

A separate deletion endpoint is implemented at `DELETE /api/privacy/synced-marketing-history`. The authenticated Connect view exposes this as a distinct destructive control rather than combining it with account disconnect.

The operation:

1. requires an authenticated workspace owner or admin;
2. requires the exact backend confirmation token `DELETE_SYNCED_HISTORY`;
3. requires the customer-facing UI to request a separate typed confirmation before calling the endpoint;
4. deletes all workspace rows from `campaign_metrics`;
5. deletes normalized KPI rows only when `source` is `google_analytics`, `google_ads`, or `meta_ads`;
6. deletes workspace anomaly records and anomaly notifications derived from synchronized reporting data;
7. preserves KPI rows whose source is `manual`;
8. does not alter or delete connector credentials;
9. returns only deleted record counts and safe status flags;
10. is covered by regression tests for confirmation, deletion scope, manual-KPI retention and role enforcement.

This control should be described precisely as deletion of **synchronized marketing/reporting history**. It is not a complete workspace, account, or privacy-rights erasure mechanism.

### Data not deleted by synchronized-history deletion

The synchronized-history deletion endpoint does not claim to delete:

- user accounts, passwords or sessions
- workspace membership or settings
- company/brand profiles
- AI requests, generated outputs or run history
- billing/customer subscription state
- competitor records or snapshots
- beta feedback
- email-delivery records
- manually entered KPI data
- connector credentials

Broader account-deletion, retention and data-subject-request procedures must therefore be finalized separately before Vexmera makes any claim of complete account or personal-data deletion.

## Private beta operating rule

For the five-company pilot, Vexmera should be described as a read-only marketing intelligence beta with human approval controls. External ad execution and autonomous campaign changes must remain disabled unless a later, separately reviewed production phase explicitly changes that policy.
