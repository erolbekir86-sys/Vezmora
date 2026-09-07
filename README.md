# Vexmera

**Vexmera 0.6.1 Private Beta**

Vexmera is an AI Marketing Officer for small and growing businesses. It brings marketing data together, identifies meaningful signals, recommends what deserves attention next, and keeps external actions behind explicit human and server-side controls.

## Product modules

- **Core** — strategic AI operator that works from company context, KPI data, signals and priorities.
- **Pulse** — strategy, anomaly detection and opportunity discovery.
- **Launch** — campaign proposals prepared for review and approval.
- **Autopilot** — controlled automation modes with policy limits and execution gates.
- **Queue** — human approval flow before external actions.
- **Connect** — read-oriented marketing and analytics integrations.

The customer-facing Command Center is Swedish-first. Core, Pulse, Launch and Autopilot remain product names.

## Private-beta safety posture

- External marketing execution is disabled by default.
- Autopilot execution requires a separate server-side enablement flag in addition to the general execution flag.
- High-risk actions are not intended for autonomous execution in the private beta.
- Google Ads and Meta Ads are described as private-beta integrations, not general-availability features.
- Marketing-site metrics are illustrative demo data and are labelled accordingly.
- Live Stripe billing must not be enabled until the sandbox catalog, webhooks, VAT/tax handling and legal terms have been verified.

## Plans

Customer-facing monthly pricing, excluding VAT:

| Plan | Price | Included users |
| --- | ---: | ---: |
| Starter | 1,499 SEK/month | 1 |
| Growth | 2,999 SEK/month | 3 |
| Scale | 5,999 SEK/month | 10 |

The application supports a 14-day Stripe Checkout trial flow. The currently documented Stripe catalog is **test-mode only**; see `STRIPE_SANDBOX_CATALOG.md` and `PRODUCTION_ENVIRONMENT.md` before touching billing configuration.

## Tech stack

- FastAPI / Python 3.12+
- static HTML/CSS/JavaScript frontend
- Neon/Postgres in production
- OpenAI-backed Core/Pulse/Launch workflows
- Stripe Checkout, signed webhooks and Customer Portal
- Google and Meta OAuth/data connectors
- Vercel deployment
- GitHub Actions CI

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload
```

On Windows PowerShell, activate the virtual environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

Never commit `.env`, API keys, OAuth secrets, database credentials or webhook secrets.

## Validation

Run the automated suite:

```bash
pytest -q
```

Validate every shipped frontend JavaScript file, matching CI:

```bash
find static -type f -name '*.js' -print0 | sort -z | xargs -0 -n1 node --check
```

The test suite also verifies server-rendered frontend shells, runtime-loaded assets and local `/static/...` references so missing or empty frontend files fail before deployment.

Run deployment preflight:

```bash
python scripts/preflight.py
```

When Stripe sandbox variables are configured, verify that all three Price IDs point to active monthly SEK prices with the expected Vexmera amounts:

```bash
python scripts/verify_stripe_catalog.py
```

## Key operational documents

- `LAUNCH_GAP_PLAN.md` — shortest safe path to the five-company private beta.
- `PILOT_READINESS_SNAPSHOT.md` — current non-secret readiness evidence and blockers.
- `FIVE_COMPANY_PILOT_RUNBOOK.md` — controlled workflow for the first five pilot companies.
- `PILOT_COMPANY_EVIDENCE_TEMPLATE.md` — safe per-company verification template without storing secrets.
- `DEPLOY_CHECKLIST.md` — deployment checks and launch blockers.
- `PRODUCTION_ENVIRONMENT.md` — environment configuration runbook.
- `STRIPE_SANDBOX_CATALOG.md` — verified test-mode Vexmera products/prices.
- `PRIVACY_POLICY_DRAFT.md` — privacy draft requiring final legal/entity details and review.
- `BETA_TERMS_DRAFT.md` — beta terms draft requiring final legal/entity details and review.

## Routing note

The public marketing site is served at `/`. The authenticated product shell is served at `/app`. The source marketing page also exists as `/static/landing.html`, but production routing is controlled by `app/public_routing.py`. Keep route changes explicit and covered by frontend smoke tests because both `/` and `/app` are launch-critical.
