# Stripe sandbox E2E evidence — 2026-09-15

This document records non-secret evidence gathered from the connected Vexmera Stripe sandbox and the production Neon database. It is intentionally limited to test-mode billing and does not authorize live billing, bank/KYC changes, tax changes or customer charges.

## Verified green

- A Vexmera test-mode Checkout Session exists and is complete.
- The completed Checkout is for the Start plan at 995 SEK/month.
- The Checkout used the current pricing version `2026-09-start-growth-pro`.
- The resulting Stripe customer and subscription were created in the Vexmera sandbox.
- The Stripe subscription is active and references the expected Start monthly price.
- Vexmera workspace 1 stores the same Stripe customer and subscription identifiers as the completed Checkout.
- Vexmera workspace 1 reports plan `start` and billing status `active`.
- The production database contains one `checkout.session.completed` billing event for the workspace.
- The production database contains one `customer.subscription.created` billing event for the workspace.
- The event counts are one each, providing current evidence that the local billing projection did not duplicate these events.
- An active default test-mode Billing Portal configuration exists for the Vexmera sandbox.
- The Billing Portal allows customer/payment-method updates and cancellation at period end according to the currently reviewed sandbox configuration.

## Still manual / orange

The following evidence is still required before declaring the entire billing browser journey green:

1. Open a Customer Portal session for the same test customer through Vexmera.
2. Verify the hosted portal loads for that customer.
3. Return from the portal to the canonical Vexmera URL.
4. Reload the authenticated billing UI and confirm the projected state remains correct.

The connected Stripe API permission available to this session can read the portal configuration but cannot create a Billing Portal session, so that final browser step has not been fabricated or marked complete.

## Safety boundary

No live-mode Stripe objects were modified. No bank details, KYC, tax settings, payout settings, real customer billing, DNS, ads, budgets or bids were changed while collecting this evidence.
