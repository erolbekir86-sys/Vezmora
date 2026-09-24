# Vexmera private beta readiness snapshot

Last reviewed: 2026-09-24

This is the canonical non-secret operational snapshot for the five-company read-only Private Beta.

## Current release baseline

- Production `main`: `0546b63a7f229b0b42726442c83a4bd88ebe4e79`
- Production domain: `https://vexmera.com`
- Vercel production deployment for the release is `READY`.
- `/health/runtime` reports the same deployment revision.
- `/health/beta-readiness` reports `private_beta_execution_safe=true` and `production_transport_safe=true`.
- External marketing execution, Autopilot execution and Meta execution scope remain disabled.
- Post-deploy runtime inspection found no active runtime-error group in the checked window.

## Verified healthy

### Product / browser

- Authenticated production desktop QA is complete with a synthetic account.
- Permanent mobile Chromium QA runs at exactly 390×844 and covers authenticated navigation, onboarding and account-privacy UI.
- Registration/login, onboarding, workspace routing, billing reads, account deletion preview, connector states and recommendation-only execution have regression/browser coverage.
- Public marketing, app, Privacy and Terms routes are live over HTTPS.

### Marketing connectors

- Google Ads production read-only sync has returned real campaign rows.
- Google Analytics has returned real rows and GA sessions are separated from paid-ad click semantics.
- Meta read-only sync distinguishes legitimate zero-data from provider/auth failures.
- Instagram and Shopify read-only connector paths are implemented.
- LinkedIn Ads read-only OAuth/reporting support is implemented and deployed with only `r_ads` and `r_ads_reporting`. Live LinkedIn customer sync remains provider-approval/configuration dependent.

### Stripe sandbox

Direct Stripe sandbox verification on 2026-09-24 confirms:

- active monthly Start / Growth / Pro prices at 995 / 1,495 / 2,995 SEK;
- all three prices carry pricing version `2026-09-start-growth-pro`;
- active default test-mode Billing Portal configuration exists;
- completed test Checkout evidence exists;
- test customers and subscriptions exist, including dedicated Vexmera billing/Portal QA records;
- signed webhook/database projection evidence is already recorded in the canonical blocker log;
- live-mode customer billing remains out of scope for the read-only pilot.

The only remaining Portal item is a manual external browser round-trip from Vexmera to Stripe-hosted Customer Portal and back. It is not a blocker for a free/read-only five-company Private Beta. It is required before customer-facing paid self-service is enabled.

## Technical blockers for five-company read-only Private Beta

**None.**

The product can be used by invited pilot companies in the defined read-only posture.

## Remaining owner/legal gates

These cannot be inferred or invented by engineering:

- final legal entity name;
- organisation/registration number if applicable;
- registered/postal address where required;
- one verified public privacy/support contact;
- approval of final longer-lived retention commitments;
- account-specific DPA/transfer review where required;
- governing law / venue approval;
- liability clause / cap approval;
- VAT/tax treatment before live paid launch;
- qualified legal review of final Privacy Policy, Beta Terms and any required DPA.

## Not pilot blockers

- LinkedIn Advertising API approval, unless a pilot specifically requires LinkedIn live data.
- Google Basic Access upgrade while current Explorer access remains sufficient.
- live advertising execution or campaign mutation.
- live paid billing when the pilot is explicitly free/read-only.

## Current recommendation

Proceed with invited B2B pilot companies now in read-only mode. Keep live billing and external campaign mutation disabled until the remaining owner/legal gates are completed.
