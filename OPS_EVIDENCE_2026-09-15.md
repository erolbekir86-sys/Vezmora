# Vexmera operational evidence — 2026-09-15

This record captures non-secret evidence gathered after merge commit `4283e156e20a61ae8d63ded1de3acc080a70d8d7` (PR #254).

## Newly verified green

- Stripe test account `Vexmera-sandlåda` has an active default Billing Portal configuration.
- Customer Portal allows customer profile updates and payment-method updates.
- Subscription cancellation is enabled at the end of the billing period with cancellation-reason collection.
- The configuration is test mode only (`livemode=false`) and returns to `https://vexmera.com`.
- The active Stripe test catalog contains exactly the current recurring SEK monthly prices for Start / Growth / Pro at 995 / 1,495 / 2,995 SEK with metadata `pricing_version=2026-09-start-growth-pro` and matching plan metadata.

## Deployment drift detected

- Repository `main` is currently `4283e156e20a61ae8d63ded1de3acc080a70d8d7` after PR #254.
- The latest verified Vercel production deployment visible during this review is still `dc42a6e1637dcd5cf1b121d1afc3a54404795333` (PR #249), state `READY`.
- Therefore PRs #250–#254 must not be described as production-deployed until Vercel serves a main revision containing them.
- This evidence-only PR intentionally creates a fresh main push after green CI so the normal GitHub-to-Vercel integration can reconcile production without bypassing deployment controls.

## Still orange

- Confirm Vercel Stripe environment variables point to the independently verified current test prices/account without exposing values.
- Run configured `verify_stripe_catalog.py` and operator preflight in the deployment environment.
- Complete a fresh test-mode Checkout -> remaining trial -> signed webhook -> billing projection -> Customer Portal -> safe return flow.
- Complete authenticated desktop/mobile browser QA. The available browser automation integration is not enabled for strict-agent mode in this session, so this gate remains open rather than being inferred from static checks.
- Final legal/privacy owner decisions and VAT/tax remain separate gates.

No DNS, credentials, secrets, live billing, bank/KYC settings, external account permissions, ads, budgets or bids were changed while collecting this evidence.
