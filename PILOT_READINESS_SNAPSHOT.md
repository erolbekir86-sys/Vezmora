# Vexmera private beta readiness snapshot

Last reviewed: 2026-09-06

This file is a non-secret operational snapshot for the five-company private beta. It records only evidence that can be safely verified without changing credentials, billing, permissions, domains, DNS, or live advertising settings.

## Verified healthy

- GitHub repository is reachable, writable through the connected GitHub integration, and the default branch is `main`.
- Latest observed `main` commit is `43d0a36058d2fc263a83cde070875a3dc48df7a9` (`Refresh pilot snapshot after frontend fail-open hardening`).
- GitHub reports the Vercel status for that commit as `success`, confirming the GitHub -> Vercel deployment path completed for the current `main` revision.
- The Python package identifies the product as `vexmera` version `0.6.1`.
- CI/test coverage includes deployment, execution safety, connector empty states, privacy controls, analytics consent, Google Ads diagnostics, billing alignment, beta readiness and public frontend asset smoke coverage.
- Public frontend smoke coverage verifies that `/` and `/app` return content and that referenced local JavaScript/CSS assets are present and non-empty.
- Frontend JavaScript syntax checks cover the landing-page scripts used by the deployed marketing page.
- Landing-page reveal effects now fail open: content is visible by default, enhanced reveal behavior is enabled only when JavaScript initializes, and frontend errors remove the reveal lock so a script failure cannot leave the page visually blank. Regression coverage protects this behavior.
- Connector empty-state handling was hardened on 2026-09-06 so successful zero-row accounts are distinguished from provider failures and HTTP errors. Existing provider warnings are preserved instead of being replaced by reassuring empty-state copy.
- Regression coverage includes campaign/ad row combinations, malformed row counts, provider errors, HTTP failures and warning preservation for connector empty-state classification.
- The pilot runbook explicitly requires recommendation-only behavior and forbids autonomous campaign, budget, bid or ad changes.
- Production database intent is confirmed from code: `DATABASE_URL`/`POSTGRES_URL` (Neon/Postgres) is preferred, while Turso is a legacy compatibility fallback.
- Database readiness diagnostics were hardened on 2026-09-06 to report backend intent and configuration booleans without exposing connection strings; tests cover PostgreSQL priority, legacy Turso identification and secret non-disclosure.
- Five-company pilot readiness diagnostics distinguish configuration blockers from manual launch gates, preventing a configuration-only pass from being mistaken for external-pilot approval.

## Current blockers requiring manual or external resolution

### 1. Direct Vercel connector visibility

Rechecked 2026-09-06 after the latest successful deployment: the connected Vercel integration still returns zero teams. A direct deployment-list request against the known Vexmera scope also returns HTTP 403 with Vercel's explicit diagnosis that the current connection is not authorized for the `vezmora` scope and must be re-authenticated to that scope or use a connection with access to it.

This is stronger evidence than the earlier zero-team symptom alone: the Vexmera team scope is still recognized by Vercel, but the current connector session cannot access it. GitHub simultaneously reports the current `main` commit's Vercel status as successful, so this remains an integration authorization problem rather than evidence that the project or deployment was deleted.

Manual action only if direct Vercel inspection is needed: reconnect/authorize the Vercel integration with access to the existing `vezmora` team/project. Do not change domains, DNS, secrets, credentials, project permissions or production settings as part of this check.

### 2. Google Ads API approval

The Vexmera MCC-to-client relationship is recorded as active, but Google Ads Basic Access remains an external prerequisite. Test Account Access is not sufficient for normal production-client reads.

Keep all advertising behavior read-only/recommendation-only until Basic Access and a real production read-only sync are independently verified. Do not enable external ad execution, campaign changes, budget changes or bid changes as part of pilot preparation.

### 3. Live connector verification

Automated coverage distinguishes legitimate empty accounts from provider failures without exposing secrets, but a real deployed walkthrough is still required for Google Ads and Meta. Verify that successful empty accounts show a clear empty state and provider/API failures show actionable, sanitized diagnostics.

### 4. Stripe sandbox deployment reconciliation

Application code and readiness diagnostics are prepared, but final sandbox reconciliation remains an external/manual gate where deployment configuration or account-level Stripe state is involved. Required checks include matching the deployed test catalog, signed webhook behavior, Checkout/trial flow and Customer Portal behavior.

Do not change Stripe keys, Price IDs, billing settings or payment configuration autonomously.

### 5. Legal/pilot sign-off

Before inviting external pilot companies, finalize the Privacy Policy and Beta Terms with concrete legal entity/contact details, retention periods and subprocessor disclosures. Legal review remains a launch gate.

### 6. Final deployed browser QA

Perform one authenticated browser pass on the actual deployed Command Center before the first pilot. Confirm onboarding, connector empty states, connector failure states, disconnect flows, account privacy controls and recommendation-only behavior in the real deployment. Also confirm the public marketing page and `/app` render correctly in a real browser after the landing reveal fail-open hardening.

## Pilot safety gate

Do not start the five-company external pilot until all of the following are true:

- the active production deployment is confirmed and health can be inspected;
- `/health/beta-readiness` reports `private_beta_execution_safe=true`;
- `pilot_readiness.configuration_ready=true` with no configuration blockers;
- external execution remains disabled;
- required pilot connectors pass read-only sync checks;
- legitimate empty connector accounts and provider failures are visually distinguishable in deployed QA;
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
