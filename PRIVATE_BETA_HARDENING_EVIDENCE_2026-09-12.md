# Private Beta hardening evidence — 2026-09-12

This file is a repository evidence snapshot for the Vexmera Private Beta release candidate. It records only code/CI evidence and must not be treated as proof of production deployment, external-provider approval, live billing approval, or completed pilot QA.

## Baseline

- Snapshot base: `main` at `11e4b61c9bec36e31f8c36042d513e4dee11608c` after PR #198.
- External ad execution and Autopilot execution remain outside this evidence and must stay disabled for the Private Beta.
- No DNS/domain settings, credentials/secrets, payment or bank details, KYC, provider-account permissions, campaign budgets or bids are changed by the hardening recorded here.

## Security and resilience changes verified in code/CI

### PR #195 — repository secret-hygiene guard

- Adds conservative CI scanning for high-confidence committed credential formats.
- Scanner output identifies file/type only and does not print detected secret values.
- CI fails before the test stage when a likely tracked credential is detected.

### PR #196 — security-header middleware idempotency

- Prevents accidental duplicate installation of the application security-header middleware.
- Keeps existing header values and routing semantics unchanged.
- Regression coverage verifies that a second installer call does not add another middleware layer.

### PR #197 — Vercel edge/application header parity

- Adds `X-Frame-Options: DENY` at the Vercel edge to match the FastAPI response policy.
- Adds `X-Permitted-Cross-Domain-Policies: none` at the Vercel edge to match the FastAPI response policy.
- Regression coverage guards the edge configuration against silent drift.
- No CSP connect/source directives were tightened as part of this change.

### PR #198 — Stripe webhook preflight ordering

- Rejects a missing `Stripe-Signature` before Stripe client creation.
- Rejects missing `STRIPE_WEBHOOK_SECRET` before Stripe client creation.
- Keeps valid signed webhook processing unchanged after the preflight checks.
- Regression coverage verifies that both deterministic failure paths occur without SDK/client initialization.
- The PR head CI run (`Vexmera CI` run 1338) completed successfully before merge.

## Evidence boundary

The items above establish repository code and automated-CI evidence only. Before an external five-company pilot, the existing launch gates still require separate evidence for:

- the exact Vercel production revision and production runtime behaviour;
- authenticated browser QA for `/app`, sign-in, onboarding, empty/error/loading states and privacy/destructive controls;
- Google Ads access approval and a controlled real read-only sync;
- a controlled Meta read-only sync plus token lifecycle/expiry behaviour;
- current Start / Growth / Pro Stripe test-mode catalog reconciliation and signed webhook/Checkout/Portal end-to-end verification;
- legal entity/contact details, retention/subprocessor decisions and legal review;
- per-company pilot evidence and stop-condition handling.

A green GitHub CI run or Ready preview is not a substitute for those deployment, provider, billing, legal or manual-pilot checks.
