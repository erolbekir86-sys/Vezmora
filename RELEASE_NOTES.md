# Vexmera 0.6.1 Private Beta — Deployment Release

Built on Vexmera 0.6 with the beta product features intact, plus:

- Vercel FastAPI entrypoint and `vercel.json`
- serverless-safe execution mode
- authenticated daily maintenance cron
- immediate processing of critical user-triggered jobs in serverless mode
- Neon/Postgres production persistence, with legacy Turso compatibility retained
- inserted-ID handling that does not rely on remote `lastrowid`
- StripeClient-based subscription billing integration
- 14-day first-customer subscription trial flow
- Stripe trial status and trial end synchronized by signed webhook handling
- Stripe Customer Portal integration
- verified **test-mode** Vexmera Starter, Growth and Scale catalog for the currently connected Stripe sandbox
- safe Stripe catalog preflight that validates active monthly SEK prices and expected amounts without printing secrets or IDs
- Google/Meta private-beta connector work with external execution kept behind explicit safety gates
- premium Vexmera marketing-site and Command Center polish aligned to the same pricing, product names and private-beta language
- Swedish-first Command Center customer copy with Core, Pulse, Launch and Autopilot retained as product names
- Python 3.12+ deployment target
- automated Python tests plus syntax validation for all shipped frontend JavaScript in GitHub Actions

## Important private-beta boundaries

- The public marketing page uses illustrative demo metrics and labels them as demo data.
- Google Ads and Meta Ads are private-beta integrations, not general-availability claims.
- External marketing execution and Autopilot execution remain disabled by default and require separate server-side enablement.
- Stripe live mode is **not** enabled by these release notes. The connected sandbox catalog is test-only, and deployment Price IDs/webhook configuration must be reconciled before a fresh end-to-end Checkout test.
- VAT/tax handling, final legal terms, the canonical production domain, Google Ads Basic Access and the five-company pilot remain launch work.

Secrets and credentials are never committed to the repository. External OpenAI/Google/Meta/SMTP/Stripe services still require the correct environment configuration in the active deployment.
