# Vexmera Private Beta blockers — current through 2026-09-16

This is the canonical current blocker list. Older checklists should defer to this file when they conflict.

## Green

- Private Beta execution posture: external execution disabled, Autopilot execution disabled, Meta execution scope disabled.
- Production transport/readiness endpoint reports safe execution and safe production transport.
- Production deployment containing PR #264 is READY on `vexmera.com`.
- Google Ads read-only production sync has returned real campaign rows.
- Meta read-only sync correctly distinguishes legitimate zero-row data from auth/provider failure.
- Current Stripe test catalog is Start 995 SEK, Growth 1,495 SEK and Pro 2,995 SEK monthly with pricing version `2026-09-start-growth-pro`.
- Stripe test Checkout evidence exists and signed billing events are persisted idempotently.
- Active default test-mode Billing Portal configuration exists.
- Customer Portal code requires owner/admin role, an attached Stripe customer, an explicit reviewed portal configuration and canonical return origin.
- Regression coverage includes the production Customer Portal return URL `https://vexmera.com/?view=team`.
- Production Checkout readiness now fails closed unless the deployed `STRIPE_PRICE_START/GROWTH/PRO` values exactly match the independently reviewed sandbox price IDs, the pricing version is current, and Stripe secret/webhook configuration is present.
- After PR #264 reached production, an authenticated synthetic workspace still reported `checkout_ready=true`; therefore the deployed Start/Growth/Pro catalog is reconciled under the stricter exact-ID gate.
- Authenticated production desktop QA completed with a synthetic account: registration, login/logout/re-login, onboarding, routing/navigation, overview, company/profile, Team/Billing reads, account-deletion preview, connector empty states and recommendation-only execution posture were exercised without connecting Google/Meta or changing external systems.
- Production billing UI rendered Start 995 SEK, Growth 1,495 SEK and Pro 2,995 SEK.
- Privacy/Terms technical drafts are aligned with the current implementation.
- Engineering retention proposal and processor/data-flow inventory are documented.

## Orange — remaining technical/manual evidence gates

1. **Real mobile viewport walkthrough**
   - verify the authenticated product at approximately 390×844;
   - confirm the existing mobile menu toggle/responsive breakpoints operate correctly in a real narrow viewport;
   - verify header controls, cards, forms, tables and modals without clipping or inaccessible controls.
   The connected browser automation completed authenticated desktop traversal but cannot set or prove a mobile viewport. Source and regression coverage contain responsive/mobile safeguards; this remains an evidence gate, not a currently reproduced code defect.

2. **Customer Portal live browser return**
   - open Customer Portal from an authenticated Vexmera test workspace that already has a Stripe test customer/subscription attached;
   - confirm the Stripe test portal opens with the reviewed configuration;
   - return to Vexmera and reload;
   - confirm billing/team state remains healthy without changing plan, payment method or cancellation.
   The Stripe sandbox contains existing test subscriptions and the reviewed portal configuration, but the available synthetic production QA workspace has no attached Stripe customer. Prior billing E2E evidence for the existing Stripe-linked test workspace does not include reusable Vexmera login credentials, and the connected Stripe permission cannot create a Billing Portal session directly. This gate must not be fabricated by attaching unrelated records or touching a real customer.

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
