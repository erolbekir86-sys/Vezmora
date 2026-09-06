# Vexmera private beta readiness snapshot

Last reviewed: 2026-09-06

This file is a non-secret operational snapshot for the five-company private beta. It records only evidence that can be safely verified without changing credentials, billing, permissions, domains, DNS, or live advertising settings.

## Verified healthy

- GitHub repository is reachable, writable through the connected GitHub integration, and the default branch is `main`.
- Latest observed `main` commit is `241b0c5df7b586e6b0d073f03f32902e8dc3f47f` (`Align pilot runbook with readiness diagnostics`).
- GitHub reports the Vercel status for that commit as `success`, confirming the GitHub -> Vercel deployment path completed for the current `main` revision.
- The Python package identifies the product as `vexmera` version `0.6.1`.
- CI/test coverage includes deployment, execution safety, connector empty states, privacy controls, analytics consent, Google Ads diagnostics, billing alignment and beta readiness.
- The pilot runbook explicitly requires recommendation-only behavior and forbids autonomous campaign, budget, bid or ad changes.
- Production database intent is confirmed from code: `DATABASE_URL`/`POSTGRES_URL` (Neon/Postgres) is preferred, while Turso is a legacy compatibility fallback.
- Database readiness diagnostics were hardened on 2026-09-06 to report backend intent and configuration booleans without exposing connection strings; tests cover PostgreSQL priority, legacy Turso identification and secret non-disclosure.
- Five-company pilot readiness diagnostics now distinguish configuration blockers from manual launch gates, preventing a configuration-only pass from being mistaken for external-pilot approval.

## Current blockers requiring manual or external resolution

### 1. Direct Vercel connector visibility

Rechecked 2026-09-06: the connected Vercel integration currently returns zero teams. Direct project listing, production runtime logs, deployment inspection and toolbar feedback therefore remain unavailable through this connection.

This does not indicate a broken deployment: GitHub reports the current `main` commit's Vercel status as successful. Treat this specifically as a ChatGPT/Vercel connector visibility or OAuth-scope issue, not as evidence that the Vexmera project is missing.

Manual action only if direct Vercel inspection is needed: reconnect/authorize the Vercel integration with access to the team/project that owns Vexmera. Do not change domains, DNS, secrets, credentials, project permissions or production settings as part of this check.

### 2. Google Ads manager link and API approval

`DEPLOY_CHECKLIST.md` records external prerequisites around the Google Ads manager link and Google Ads API access. Keep all advertising behavior read-only/recommendation-only until those prerequisites are independently confirmed.

Do not enable external ad execution, campaign changes, budget changes or bid changes as part of pilot preparation.

### 3. Stripe sandbox deployment reconciliation

Application code and readiness diagnostics are prepared, but final sandbox reconciliation remains an external/manual gate where deployment configuration or account-level Stripe state is involved. Required checks include matching the deployed test catalog, signed webhook behavior, Checkout/trial flow and Customer Portal behavior.

Do not change Stripe keys, Price IDs, billing settings or payment configuration autonomously.

### 4. Legal/pilot sign-off

Before inviting external pilot companies, finalize the Privacy Policy and Beta Terms with concrete legal entity/contact details, retention periods and subprocessor disclosures. Legal review remains a launch gate.

### 5. Final deployed browser QA

Perform one authenticated browser pass on the actual deployed Command Center before the first pilot. Confirm onboarding, connector empty states, disconnect flows, account privacy controls and recommendation-only behavior in the real deployment.

## Pilot safety gate

Do not start the five-company external pilot until all of the following are true:

- the active production deployment is confirmed and health can be inspected;
- `/health/beta-readiness` reports `private_beta_execution_safe=true`;
- `pilot_readiness.configuration_ready=true` with no configuration blockers;
- external execution remains disabled;
- required pilot connectors pass read-only sync checks;
- Stripe sandbox readiness passes if billing is included in the pilot;
- Privacy Policy and Beta Terms are finalized;
- authenticated browser QA passes.

## Next safe autonomous work

When direct Vercel visibility becomes available, the next low-risk checks are:

1. inspect production runtime errors and non-secret health diagnostics;
2. confirm the active deployment revision matches GitHub `main`;
3. verify execution-safety diagnostics remain safe;
4. inspect unresolved Vercel toolbar feedback;
5. update this snapshot only when evidence changes.
