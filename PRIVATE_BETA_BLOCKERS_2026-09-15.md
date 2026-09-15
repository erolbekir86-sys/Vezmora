# Vexmera Private Beta blockers — 2026-09-15

This is the canonical current blocker list. Older checklists should defer to this file when they conflict.

## Green

- Private Beta execution posture: external execution disabled, Autopilot execution disabled, Meta execution scope disabled.
- Production transport/readiness endpoint reports safe execution and safe production transport.
- Latest verified production deployment after PR #255 reached READY on vexmera.com with no runtime error group in the checked window.
- Google Ads read-only production sync has returned real campaign rows.
- Meta read-only sync correctly distinguishes legitimate zero-row data from auth/provider failure.
- Current Stripe test catalog is Start 995 SEK, Growth 1,495 SEK and Pro 2,995 SEK monthly with pricing version `2026-09-start-growth-pro`.
- Stripe test Checkout evidence exists for Start 995 SEK and completed successfully.
- Resulting Stripe subscription is active and uses the current Start price/pricing version.
- Vexmera workspace billing projection matches the Stripe customer/subscription and reports active status.
- Signed billing events are persisted idempotently for `checkout.session.completed` and `customer.subscription.created`.
- Active default test-mode Billing Portal configuration exists.
- Customer Portal code requires owner/admin role, an attached Stripe customer, an explicit reviewed portal configuration and canonical return origin.
- Regression coverage now includes the production Customer Portal return URL `https://vexmera.com/?view=team`.
- Privacy/Terms technical drafts are aligned with the current implementation.
- Engineering retention proposal and processor/data-flow inventory are documented.

## Orange — real remaining technical/manual gates

1. **Authenticated browser QA**
   - desktop authenticated walkthrough;
   - mobile viewport walkthrough;
   - registration/login/reset/session behavior;
   - onboarding/routing/navigation;
   - privacy/deletion preview;
   - safe connector states;
   - recommendation-only execution posture.
   Current automated browser tooling is blocked before interaction by the browser platform/security layer, so this gate is not falsely marked green.

2. **Customer Portal live browser return**
   - open Customer Portal from an authenticated Vexmera workspace using the test customer;
   - confirm Stripe session opens with the reviewed configuration;
   - return to Vexmera and reload;
   - confirm billing/team view remains healthy.
   Code/configuration behavior is covered by regression tests, but the live authenticated browser round trip remains unverified.

3. **Production Stripe environment reconciliation**
   - confirm deployed `STRIPE_PRICE_START/GROWTH/PRO` resolve to the independently verified test prices;
   - confirm deployed Stripe secret belongs to the same sandbox account;
   - run deployment-context catalog/preflight and require success.
   Existing successful Checkout strongly supports configuration correctness, but secret/env identity should still be verified explicitly rather than inferred.

## Orange — owner/legal gates

- legal entity name;
- registration/organisation number if applicable;
- registered/postal address where required;
- verified public privacy/support email;
- final longer-lived retention commitments after engineering scheduling is confirmed;
- processor/account DPA and transfer review where required;
- governing law/venue;
- liability clause/cap;
- VAT/tax treatment before live paid launch;
- final qualified review/approval of Privacy Policy, Beta Terms and any required DPA.

## Not a five-company read-only pilot blocker

- Google OAuth Brand Verification/Basic Access upgrade unless current Explorer quota/functionality becomes insufficient.
- Live advertising execution, campaign mutation, budgets or bids. These remain intentionally disabled.
- Live paid billing if the pilot is explicitly run without live billing and customer-facing terms/UI accurately reflect that state.
