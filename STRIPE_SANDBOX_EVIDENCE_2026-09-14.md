# Stripe sandbox evidence — 2026-09-14

This note records only non-secret, read-only evidence from the connected Vexmera Stripe sandbox. It must not contain secret keys, webhook signing secrets, customer data, account identifiers, payment details, or live-mode billing data.

## Verified today

- The connected Stripe context is test mode / sandbox.
- The currently connected sandbox exposes no Billing Portal configuration (`data=[]`).
- This confirms the remaining Customer Portal blocker is configuration/policy, not an unknown code path.
- Vexmera already implements Stripe Checkout, signed webhook handling and Customer Portal session creation in application code.
- PR #233 was merged to `main` after green CI and tightens billing readiness so whitespace-only Stripe key/webhook configuration is treated as unconfigured.

## Still intentionally blocked

A test-mode Billing Portal configuration must not be invented automatically because its customer-facing policy is an owner/business decision. Before creating it, the owner must decide at minimum whether pilot customers may:

- cancel subscriptions themselves;
- switch plans themselves;
- update payment methods themselves.

VAT/tax treatment, live-mode billing, bank details and KYC remain outside the Private Beta automation scope.

## Next safe technical steps

1. Keep Stripe work in test mode only.
2. Merge any additional fail-closed runtime hardening only after fresh green CI.
3. After the owner selects Billing Portal policy, create/configure the test-mode portal.
4. Run a fresh end-to-end sandbox Checkout -> remaining trial -> signed webhook -> workspace billing projection -> Customer Portal -> safe return test.
5. Confirm one idempotent billing event for the intended test workspace without copying webhook payloads or secrets into evidence.
