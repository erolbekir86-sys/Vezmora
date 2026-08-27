# Vexmera 0.6.1 Private Beta — Deployment Release

Built on Vexmera 0.6 with the beta product features intact, plus:

- Vercel FastAPI entrypoint and `vercel.json`
- serverless-safe execution mode
- authenticated daily maintenance cron
- immediate processing of critical user-triggered jobs in serverless mode
- optional Turso remote SQLite-compatible persistence
- inserted-ID handling that does not rely on remote `lastrowid`
- StripeClient-based billing integration
- real Stripe sandbox Price IDs for Starter, Growth and Scale
- enforced 14-day first-customer subscription trial
- Stripe trial status and trial end synchronized by webhook
- Stripe Customer Portal retained
- Python 3.12+ deployment target
- 14 automated tests passing

Secrets are not included in the release archive. External Turso/OpenAI/Google/Meta/SMTP calls still require credentials in the deployment environment.
