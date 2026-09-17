# Vexmera Private Beta blockers — current through 2026-09-17

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
- Production Checkout readiness fails closed unless the deployed `STRIPE_PRICE_START/GROWTH/PRO` values exactly match the independently reviewed sandbox price IDs, the pricing version is current, and Stripe secret/webhook configuration is present.
- After PR #264 reached production, an authenticated synthetic workspace still reported `checkout_ready=true`; therefore the deployed Start/Growth/Pro catalog is reconciled under the stricter exact-ID gate.
- Authenticated production desktop QA completed with a synthetic account: registration, login/logout/re-login, onboarding, routing/navigation, overview, company/profile, Team/Billing reads, account-deletion preview, connector empty states and recommendation-only execution posture were exercised without connecting Google/Meta or changing external systems.
- Production billing UI rendered Start 995 SEK, Growth 1,495 SEK and Pro 2,995 SEK.
- A dedicated Stripe sandbox customer and Start trial subscription are now attached to synthetic production QA workspace 6. Stripe reports the subscription as Start/trialing, the signed `customer.subscription.created` webhook was accepted by production, and the production database stores the matching Stripe customer ID, subscription ID, Start plan, trialing status and trial end.
- Real mobile browser evidence is complete. PR #266 added a permanent Chromium CI gate at exactly 390×844. The test verifies the unauthenticated shell, establishes a synthetic authenticated session, completes onboarding, exercises the responsive menu, traverses all 12 primary product views, opens the account-privacy surface and fails on page-level horizontal overflow.
- Vexmera CI run #1508 passed with the 390×844 browser gate enabled.
- PR #266 is merged to `main`, and production deployment `dpl_3jcimr33BamsNTJFvvpvUQJFYXtD` for commit `32821b9f830b624a5453b745b750f900d12ca22f` is READY.
- Privacy/Terms technical drafts are aligned with the current implementation.
- Engineering retention proposal and processor/data-flow inventory are documented.

## Technical blockers for a five-company read-only Private Beta

**None.**

The former mobile viewport evidence gate is closed by the permanent 390×844 Chromium CI test. The former Customer Portal prerequisite gap is also closed: a dedicated synthetic production QA workspace now has a matching Stripe sandbox customer/subscription, the signed subscription webhook reached production, the database projection matches Stripe, the reviewed Portal configuration exists, and the canonical Portal return URL is regression-tested.

## Manual, non-blocking spot-check before live paid self-service

- Open Stripe Customer Portal from the dedicated synthetic/test workspace and follow the external browser return back to Vexmera Team/Billing without changing plan, payment method or cancellation.
- The currently connected browser automation refuses the external Stripe Portal action under its safety controls, and the connected Stripe API permission cannot create Billing Portal sessions directly. No successful external round trip is therefore claimed or fabricated.
- This is not a blocker for the five-company read-only Private Beta while live customer billing is intentionally out of scope. It becomes a required manual acceptance check before customer-facing paid self-service is enabled.

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
