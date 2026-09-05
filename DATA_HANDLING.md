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

A backend self-service disconnect flow is now implemented for Google and Meta at `POST /api/connectors/{provider}/disconnect`.

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

A separate, explicitly confirmed historical-data deletion flow is still required before Vexmera can promise one-click deletion of all previously synchronized marketing data. Customer-facing text must distinguish clearly between:

- **Disconnect account:** remove stored connector credentials and stop future sync access.
- **Delete synchronized history:** separately delete retained campaign/KPI history after an explicit destructive confirmation.

Until the second flow is implemented and tested, Vexmera must not claim that disconnecting an account also purges all historical marketing data.

## Private beta operating rule

For the five-company pilot, Vexmera should be described as a read-only marketing intelligence beta with human approval controls. External ad execution and autonomous campaign changes must remain disabled unless a later, separately reviewed production phase explicitly changes that policy.
