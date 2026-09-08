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
- Live Stripe billing must not be enabled until the public pricing model, backend plan model, Stripe sandbox catalog, webhooks, VAT/tax handling and legal terms have been reconciled and verified.

## Plans and billing migration

The public marketing site currently advertises these monthly prices, excluding VAT:

| Plan | Public price |
| --- | ---: |
| Start | 995 SEK/month |
| Growth | 1,495 SEK/month |
| Pro | 2,995 SEK/month |

The backend and historical verified Stripe sandbox catalog still use the older **Starter / Growth / Scale** model. New Stripe Checkout sessions are intentionally blocked by the pricing-reconciliation safety guard until the public pricing, backend plan metadata, tests and Stripe sandbox catalog all describe the same model.

Do not bypass that guard and do not treat the historical Starter / Growth / Scale Price IDs as the current pilot checkout catalog. See `STRIPE_SANDBOX_CATALOG.md`, `PILOT_RUNBOOK.md` and `PRODUCTION_ENVIRONMENT.md` before touching billing configuration.

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

`python scripts/verify_stripe_catalog.py` verifies the historical sandbox catalog described in `STRIPE_SANDBOX_CATALOG.md`. Do not use that result as evidence that the current public Start / Growth / Pro pricing is checkout-ready; pricing reconciliation must happen first.

## Key operational documents

- `LAUNCH_GAP_PLAN.md` — shortest safe path to the five-company private beta.
- `PILOT_READINESS_SNAPSHOT.md` — current non-secret readiness evidence and blockers.
- `FIVE_COMPANY_PILOT_RUNBOOK.md` — controlled workflow for the first five pilot companies.
- `PILOT_COMPANY_EVIDENCE_TEMPLATE.md` — safe per-company verification template without storing secrets.
- `DEPLOY_CHECKLIST.md` — deployment checks and launch blockers.
- `PRODUCTION_ENVIRONMENT.md` — environment configuration runbook.
- `STRIPE_SANDBOX_CATALOG.md` — historical verified test-mode catalog; not the current public pricing model.
- `PRIVACY_POLICY_DRAFT.md` — privacy draft requiring final legal/entity details and review.
- `BETA_TERMS_DRAFT.md` — beta terms draft requiring final legal/entity details and review.

## Routing note

The public marketing site is served at `/`. The authenticated product shell is served at `/app`. The source marketing page also exists as `/static/landing.html`, but production routing is controlled by `app/public_routing.py`. Keep route changes explicit and covered by frontend smoke tests because both `/` and `/app` are launch-critical.
