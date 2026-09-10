# Vexmera pilot operator quickstart

Use this before onboarding any of the first five pilot companies. It is intentionally short and points back to `FIVE_COMPANY_PILOT_RUNBOOK.md` for the full process.

## One command first

Run the consolidated read-only check against production:

```bash
python scripts/pilot_go_no_go.py --base-url https://vexmera.com
```

This combines machine-checkable local configuration checks with GET-only public checks for execution locks, production deployment identity and legal-page discoverability. The public runtime gate verifies that the deployed service identifies as Vercel production and exposes an identifiable deployment revision. The local configuration section verifies non-secret facts such as whether persistent remote storage and required internal security configuration are configured; it does **not** claim that a live database connection or third-party account access has been proven. No secret values are returned.

The command does not send credentials, mutate provider data, change campaigns, or approve the pilot.

Interpretation:

- exit code `0` / `status: machine_checks_clear`: machine checks are clear only; continue with manual gates below.
- non-zero exit code / `status: blocked`: stop onboarding and resolve the reported blocker first.
- `pilot_ready` remains intentionally unset because final pilot approval requires human verification.

Common public runtime blockers include `runtime_unreachable`, `runtime_not_vercel`, `runtime_not_production`, `deployment_revision_unknown` and any failed Private Beta execution lock. Configuration blockers are reported separately. Treat each blocker as a stop condition until the underlying issue is understood and fixed. Never copy secret values into pilot evidence while investigating.

## Manual gates that still matter

Before company 1, confirm the current runbook evidence for:

- authenticated browser QA on the deployed app,
- Privacy Policy and Terms review for the intended pilot,
- Google Ads external approval / manager linking if required,
- pricing/backend/Stripe sandbox reconciliation before any checkout test,
- production transport, remote database, transactional email and OAuth configuration,
- live read-only connector verification for the providers included in the pilot,
- production observability/log review when the Vercel project is visible to the connected operator tooling.

Do not bypass a safety gate simply to make the pilot pass.

## Per-company minimum

For each company, verify:

1. signup/login and the intended onboarding path work,
2. connector OAuth returns to Vexmera and shows the correct state,
3. valid zero-row data is shown as an empty state, not an error,
4. API/auth failures are shown as failures, not healthy empty data,
5. live connected data is clearly distinguished from demo data,
6. recommendations remain proposals only and external execution stays locked,
7. disconnect works,
8. no secret/token values appear in UI, diagnostics, logs, screenshots or support notes,
9. Google Analytics sessions are not treated as paid-ad clicks.

## Immediate stop conditions

Stop onboarding if any execution lock is unexpectedly enabled, tenant isolation looks wrong, provider scopes become broader than expected, a secret/token is exposed, live billing is reached unexpectedly, production runtime identity cannot be verified, or production data is presented misleadingly.

For full evidence capture, billing-sandbox rules, privacy/deletion checks, completion criteria and the five-company roster, use `FIVE_COMPANY_PILOT_RUNBOOK.md`.
