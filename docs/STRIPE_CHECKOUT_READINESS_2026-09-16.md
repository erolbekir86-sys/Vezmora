# Stripe Checkout readiness hardening — 2026-09-16

Checkout readiness now fails closed unless the deployed environment points at the exact independently reviewed Vexmera sandbox Start/Growth/Pro Stripe catalog, the current pricing-version marker is present, and Stripe secret/webhook configuration is non-empty.

This closes the gap where non-empty but stale or mistyped price IDs could previously allow `checkout_ready=true`.

No Stripe secret values are exposed. No live billing, customer subscription, payment method, DNS, bank/KYC, ad execution, budgets or bids are changed.
