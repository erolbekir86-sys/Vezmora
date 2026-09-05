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

This control should be described precisely as deletion of **synchronized marketing/reporting history**. It is not the same operation as deleting a Vexmera account.

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

These categories are intentionally outside the scoped reporting-history control. Broader deletion is handled by the separate account-deletion flow described below.

## Full self-service account deletion

Vexmera implements a guarded full account-deletion flow with a preview at `GET /api/privacy/account-deletion-preview` and irreversible deletion at `DELETE /api/privacy/account`.

Before deletion, the authenticated customer UI shows blockers and deletion scope. The final request requires both the current account password and the exact confirmation phrase `DELETE MY ACCOUNT`.

Deletion is blocked when:

- an owned workspace still has another member; or
- an owned workspace has an attached Stripe subscription whose state is not treated as inactive.

When deletion is allowed, Vexmera:

1. re-authenticates the current password;
2. re-checks blockers immediately before local deletion;
3. best-effort revokes Google and Meta OAuth tokens for solo-owned workspaces;
4. deletes solo-owned workspaces and their database-cascaded workspace data;
5. removes the user's memberships from workspaces owned by other users while preserving those shared business workspaces;
6. deletes the user account and password credentials;
7. removes sessions through account deletion and clears the active session cookie;
8. removes pending invitations for the account email;
9. removes queued application email addressed to the account email;
10. returns only safe deletion counts and revocation status.

Third-party billing or compliance records are **not** represented as guaranteed deleted. Stripe and other processors may retain records where required for accounting, fraud prevention, dispute handling, security or legal obligations. Vexmera's public privacy documentation must describe this distinction accurately.

## Website analytics consent

The authenticated Vexmera web application uses a privacy-first Google Analytics consent flow.

Current behavior:

- Google Analytics is not embedded directly in the initial HTML;
- `analytics_storage`, `ad_storage`, `ad_user_data`, and `ad_personalization` default to `denied`;
- the Google Analytics script is loaded only after an explicit `granted` analytics choice;
- Google Signals is disabled;
- ad-personalization signals are disabled;
- customers can reopen Cookieinställningar and change the analytics choice later;
- when analytics is denied or consent is withdrawn, Vexmera updates consent to denied and performs best-effort removal of first-party `_ga` cookies visible to the application origin.

The consent implementation is covered by regression tests that verify no direct pre-consent Google Analytics tag is shipped in the authenticated HTML and that the consent JavaScript remains syntax-checked in CI.

This technical consent mechanism does not replace the need for final public cookie/privacy wording and legal review.

## Retention and external processors still requiring final policy decisions

The codebase now has customer controls for connector credential deletion, synchronized-history deletion and full account deletion, but **production retention periods are not yet finalized** for every retained category.

Before external pilot onboarding, Vexmera should document and legally review at least:

- default retention for account and workspace data while an account remains active;
- retention of AI run history and generated outputs;
- retention of competitor snapshots and beta feedback;
- operational/security log retention;
- email-delivery/outbox retention;
- backups and database recovery retention where applicable;
- processor-specific retention that Vexmera cannot directly erase on demand;
- the final list and roles of hosting, database, AI, billing, email, analytics and advertising-platform providers.

No public claim should state a concrete retention period until the production policy has been intentionally selected and matched to actual infrastructure behavior.

## Private beta operating rule

For the five-company pilot, Vexmera should be described as a read-only marketing intelligence beta with human approval controls. External ad execution and autonomous campaign changes must remain disabled unless a later, separately reviewed production phase explicitly changes that policy.
