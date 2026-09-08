# Vexmera pilot operator quickstart

Use this before onboarding any of the first five pilot companies. It is intentionally short and points back to `FIVE_COMPANY_PILOT_RUNBOOK.md` for the full process.

## One command first

Run the consolidated read-only check against production:

```bash
python scripts/pilot_go_no_go.py --base-url https://vexmera.com
```

This performs machine-checkable configuration checks plus GET-only public checks for execution locks and legal-page discoverability. It does not send credentials, mutate provider data, or approve the pilot.

Interpretation:

- exit code `0` / `status: machine_checks_clear`: machine checks are clear only; continue with manual gates below.
- non-zero exit code / `status: blocked`: stop onboarding and resolve the reported blocker first.
- `pilot_ready` remains intentionally unset because final pilot approval requires human verification.

## Manual gates that still matter

Before company 1, confirm the current runbook evidence for:

- authenticated browser QA on the deployed app,
- Privacy Policy and Terms review for the intended pilot,
- Google Ads external approval / manager linking if required,
- pricing/backend/Stripe sandbox reconciliation before any checkout test,
- production transport, remote database, transactional email and OAuth configuration,
- live read-only connector verification for the providers included in the pilot.

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

Stop onboarding if any execution lock is unexpectedly enabled, tenant isolation looks wrong, provider scopes become broader than expected, a secret/token is exposed, live billing is reached unexpectedly, or production data is presented misleadingly.

For full evidence capture, billing-sandbox rules, privacy/deletion checks, completion criteria and the five-company roster, use `FIVE_COMPANY_PILOT_RUNBOOK.md`.
