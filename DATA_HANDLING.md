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

## Disconnect and deletion status

A dedicated customer-facing connector disconnect/revoke-and-delete flow is not yet implemented in the current beta codebase. This is a release-readiness gap and must be completed before Vexmera promises self-service connector deletion or immediate OAuth revocation.

Until that feature exists, pilot documentation and customer-facing legal text must not claim that a user can fully purge connector credentials from the product with a single in-app action.

The intended future disconnect flow should:

1. require an authenticated workspace owner/admin;
2. revoke the provider token where the provider supports revocation;
3. remove or invalidate the stored encrypted connector secret;
4. mark the connector disconnected;
5. clearly define whether previously synced campaign/KPI history is retained or deleted;
6. provide a separate explicit data-deletion path for retained historical data;
7. avoid exposing secrets in success/error responses;
8. be covered by regression tests.

## Private beta operating rule

For the five-company pilot, Vexmera should be described as a read-only marketing intelligence beta with human approval controls. External ad execution and autonomous campaign changes must remain disabled unless a later, separately reviewed production phase explicitly changes that policy.
