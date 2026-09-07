# Vexmera Stripe sandbox catalog

This file contains **test-mode identifiers only**. They are not secrets and must never be used with a live Stripe secret key.

Verified in the currently connected Stripe test account on 2026-09-05.

> **Pricing migration blocker (2026-09-08):** The public marketing site now advertises the newer **Start / Growth / Pro** pricing model, while this verified Stripe sandbox catalog still represents the older **Starter / Growth / Scale** model. Treat the Price IDs below as historical verified sandbox evidence only. Do not use them for a new pilot Checkout flow until the sandbox catalog, backend plan model, public pricing copy, and billing tests have been reconciled to one approved pricing model.

| Plan | Product | Monthly test price | Amount | Billing |
| --- | --- | --- | ---: | --- |
| Starter | `prod_VCfreksk5HKWTi` | `price_1UCGVX32EFR9j6MxSP6VB2TF` | 1,499 SEK | monthly recurring |
| Growth | `prod_VCfrRfoElzhsg3` | `price_1UCGVf32EFR9j6Mx0fCKTHzK` | 2,999 SEK | monthly recurring |
| Scale | `prod_VCfrwmIv1EbCVX` | `price_1UCGVm32EFR9j6MxFOxJD3zp` | 5,999 SEK | monthly recurring |

All three prices were verified as:

- `livemode=false`
- active
- currency `sek`
- recurring every 1 month
- exact unit amounts `149900`, `299900`, and `599900` öre
- attached to Vexmera-branded test products with plan metadata

## Next sandbox steps

1. Reconcile and approve one canonical product/pricing model across the public site, backend plan definitions, tests, and Stripe sandbox before running new Checkout tests.
2. Create or verify matching **test-mode** Stripe products/prices for that approved model; do not modify live billing.
3. Configure the Vercel **test/sandbox** billing environment only after the new test Price IDs have been independently verified.
4. Confirm `STRIPE_SECRET_KEY` belongs to the same Stripe test account.
5. Create or reconcile the test webhook endpoint for `<VEZMORA_APP_URL>/api/billing/webhook`.
6. Run `python scripts/verify_stripe_catalog.py` only after its expected catalog has been updated to the approved sandbox model.
7. Run one fresh Checkout flow per plan using test cards.
8. Confirm the 14-day trial, signed webhook processing, workspace plan update, Customer Portal, cancellation, and failed-payment handling.

Do not copy these IDs into Stripe live mode. Live-mode products/prices should only be created after pricing, VAT/tax handling, legal terms, and the canonical production domain have been finalized.
