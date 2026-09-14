# Stripe sandbox evidence — 2026-09-14

This note records only non-secret evidence from the connected Vexmera Stripe sandbox. It must not contain secret keys, webhook signing secrets, customer data, payment details, or live-mode billing data.

## Verified today

- The connected Stripe context is test mode / sandbox.
- The connected sandbox currently exposes no Billing Portal configuration (`data=[]`).
- Vexmera implements Stripe Checkout, signed webhook handling and Customer Portal session creation in application code.
- PR #233 was merged after green CI and makes billing readiness reject whitespace-only Stripe key/webhook configuration.
- PR #234 was merged after green CI and extends the same fail-closed handling to Stripe runtime keys, price ids and webhook-secret use.
- The latest verified production baseline before this policy change is `1b3e5e9722acc44577d1b91a4e275e2be5e4c33f`; its Vercel production deployment is `READY`, and no runtime-error group was found in the checked one-hour window.

## Owner-approved Private Beta portal policy

The owner approved the following sandbox policy on 2026-09-14:

- customers may update their payment method;
- customers may cancel their subscription themselves;
- cancellation takes effect at the end of the current paid period or trial;
- self-service plan changes are disabled during Private Beta;
- cancellation does not delete the Vexmera account or account data;
- no automatic refund policy is introduced as part of portal setup.

The detailed operational contract lives in `STRIPE_PORTAL_POLICY.md`.

## Remaining sandbox blocker

The policy decision is complete, but the Stripe sandbox still has no Billing Portal configuration. The currently connected Stripe tool surface can read portal configurations but does not expose creation/update of a portal configuration, so no account-side portal mutation was attempted from this run.

Vexmera now prepares to fail closed unless `STRIPE_BILLING_PORTAL_CONFIGURATION_ID` points to the explicitly reviewed test-mode configuration. This prevents accidental fallback to an unknown account-default portal policy.

VAT/tax treatment, live-mode billing, bank details and KYC remain outside the Private Beta automation scope.

## Next safe technical steps

1. Keep Stripe work in test mode only.
2. Require fresh green CI for the portal-policy guardrails.
3. Create the sandbox Billing Portal configuration with the approved policy when an authorized Stripe write surface is available.
4. Set only the resulting non-secret portal configuration id in the intended test deployment environment.
5. Run a fresh end-to-end sandbox Checkout -> remaining trial -> signed webhook -> workspace billing projection -> Customer Portal -> safe return test.
6. Confirm one idempotent billing event for the intended test workspace without copying webhook payloads or secrets into evidence.
