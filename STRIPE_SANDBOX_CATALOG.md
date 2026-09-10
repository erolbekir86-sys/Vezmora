# Vexmera Stripe sandbox catalog

This file preserves **historical test-mode evidence only**. The identifiers below are not secrets, but they must never be used with a live Stripe secret key and must not be reused for the current Checkout model.

Historical catalog verified in the connected Stripe test account on 2026-09-05.

> **Historical catalog only:** These Price objects represent the older **Starter / Growth / Scale** model. Vexmera now uses the canonical **Start / Growth / Pro** model at 995 / 1,495 / 2,995 SEK per month. The historical Price IDs below are retained only as audit/migration evidence and must not be configured for new private-beta Checkout sessions.

## Historical verified catalog

| Historical plan | Product | Historical monthly test price | Amount | Billing |
| --- | --- | --- | ---: | --- |
| Starter | `prod_VCfreksk5HKWTi` | `price_1UCGVX32EFR9j6MxSP6VB2TF` | 1,499 SEK | monthly recurring |
| Growth | `prod_VCfrRfoElzhsg3` | `price_1UCGVf32EFR9j6Mx0fCKTHzK` | 2,999 SEK | monthly recurring |
| Scale | `prod_VCfrwmIv1EbCVX` | `price_1UCGVm32EFR9j6MxFOxJD3zp` | 5,999 SEK | monthly recurring |

Those historical Prices were verified as:

- `livemode=false`
- active
- currency `sek`
- recurring every 1 month
- exact historical unit amounts `149900`, `299900`, and `599900` öre
- attached to Vexmera-branded test products with plan metadata

## Current approved code model

The codebase, marketing site and customer-facing billing UI now use:

| Current plan | Required monthly sandbox amount | Environment variable |
| --- | ---: | --- |
| Start | 995 SEK / `99500` öre | `STRIPE_PRICE_START` |
| Growth | 1,495 SEK / `149500` öre | `STRIPE_PRICE_GROWTH` |
| Pro | 2,995 SEK / `299500` öre | `STRIPE_PRICE_PRO` |

The exact pricing-version approval marker for this model is:

- `VEZMORA_STRIPE_PRICING_VERSION=2026-09-start-growth-pro`

Do **not** set that marker merely because Price IDs exist. It is the final explicit approval gate after the current three sandbox Prices have been independently checked.

## Canonical verification

Run this command in the same configured environment that will serve the private beta:

```bash
python scripts/verify_stripe_catalog.py
```

The verifier is read-only and uses the current Start / Growth / Pro expectations from `app/pricing.py`. It checks that each configured Price:

- is the same Price referenced by the configured environment variable;
- is active;
- has `livemode=false`;
- uses currency `sek`;
- is a recurring Price;
- recurs every one month;
- has the exact current amount for its plan.

It also reports whether the exact current pricing-version marker matches. It never returns the Stripe secret, configured Price IDs, Product IDs, raw Stripe payloads or raw Stripe exceptions.

A successful `catalog_ok=true` is necessary evidence for the current sandbox catalog. Final `ok=true` additionally requires the exact pricing-version marker.

## Remaining sandbox steps

1. Create or independently verify matching **test-mode** Start / Growth / Pro products and Prices at 995 / 1,495 / 2,995 SEK monthly. Do not modify live billing.
2. Configure `STRIPE_PRICE_START`, `STRIPE_PRICE_GROWTH`, and `STRIPE_PRICE_PRO` in the intended Vercel environment only after the new test Price IDs have been independently identified.
3. Confirm `STRIPE_SECRET_KEY` belongs to the same Stripe test account as all three configured Price IDs.
4. Run `python scripts/verify_stripe_catalog.py` and require `catalog_ok=true`.
5. Only after the catalog check passes, set `VEZMORA_STRIPE_PRICING_VERSION=2026-09-start-growth-pro` and rerun the verifier.
6. Create or reconcile the test webhook endpoint for `<VEZMORA_APP_URL>/api/billing/webhook`.
7. Run one fresh Checkout flow per plan using Stripe test payment methods.
8. Confirm the 14-day trial, signed webhook processing, workspace plan update, Customer Portal, cancellation and failed-payment handling.

Do not copy the historical IDs above into the current configuration or into Stripe live mode. Live-mode products/prices remain a separate future decision after VAT/tax handling, legal terms and the canonical production domain have been finalized.
