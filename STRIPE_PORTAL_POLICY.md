# Vexmera Private Beta Stripe Customer Portal policy

Approved by the owner on 2026-09-14 for the **Stripe test-mode / sandbox** Private Beta only.

This policy is intentionally conservative. It gives pilot customers control over payment details and cancellation without enabling plan-change behavior that has not yet been proven end to end.

## Approved customer actions

- **Update payment method:** allowed.
- **Cancel subscription:** allowed.
- **Cancellation timing:** cancellation takes effect at the end of the current paid period or at the end of the active trial, not immediately.
- **Change subscription plan:** disabled during Private Beta.

## Explicitly not part of cancellation

- Cancellation must not automatically delete the Vexmera account.
- Cancellation must not automatically delete synchronized marketing history or other account data.
- Cancellation must not trigger an automatic refund policy.
- Account/data deletion remains a separate privacy action with its own safeguards.

## Vexmera application guardrails

- An active Stripe subscription cannot start a second Checkout flow merely to switch Start/Growth/Pro plans.
- Customer Portal sessions must be pinned to an explicitly reviewed Stripe Billing Portal configuration through `STRIPE_BILLING_PORTAL_CONFIGURATION_ID`.
- If that configuration id is missing or effectively blank, Customer Portal creation fails closed instead of falling back to an unknown Stripe account-default policy.
- The configuration id is not a secret, but it must refer to the reviewed **test-mode** portal configuration during Private Beta.

## Required Stripe sandbox configuration

The reviewed sandbox configuration must implement all of the following before the Customer Portal E2E gate can pass:

1. payment-method updates enabled;
2. subscription cancellation enabled;
3. cancellation effective at period/trial end;
4. subscription plan updates disabled;
5. no live-mode configuration changes;
6. no automatic refund rule introduced as part of this setup.

## Later public-launch review

Self-service plan changes can be reconsidered after Private Beta evidence exists. A likely later policy is immediate upgrade with clearly defined proration and downgrade at the next billing period, but that is **not approved for Private Beta** and must not be enabled implicitly.
