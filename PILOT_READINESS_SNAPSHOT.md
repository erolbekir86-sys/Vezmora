# Vexmera private beta readiness snapshot

Last reviewed: 2026-09-08

This file is a non-secret operational snapshot for the five-company private beta. It records only evidence that can be safely verified without changing credentials, billing, permissions, domains, DNS, or live advertising settings.

## Verified healthy

- GitHub repository is reachable and writable through the connected GitHub integration; the default branch is `main`.
- Latest observed `main` commit before this snapshot refresh is `dd9401c7b03722d0bb1de7ecd5d57ad29eecbdf8` (`Add GA metric semantics evidence to pilot template`).
- GitHub Actions `Vexmera CI` run 414 for that commit completed successfully on 2026-09-08.
- GitHub reports the Vercel deployment status for that commit as `success`, confirming the GitHub -> Vercel deployment path completed for the observed `main` revision.
- The Python package identifies the product as `vexmera` version `0.6.1`.
- CI/test coverage includes deployment, execution safety, connector empty states, privacy controls, analytics consent, Google Ads diagnostics, billing alignment, beta readiness and public frontend asset smoke coverage.
- Public frontend smoke coverage verifies that `/` and `/app` return content and that referenced local JavaScript/CSS assets are present and non-empty.
- Frontend JavaScript syntax checks cover the landing-page scripts used by the deployed marketing page.
- Landing-page reveal effects fail open: content is visible by default, enhanced reveal behavior is enabled only when JavaScript initializes, and frontend errors remove the reveal lock so a script failure cannot leave the page visually blank.
- Connector empty-state handling distinguishes successful zero-row accounts from provider failures, HTTP errors and missing Google Ads configuration. Provider warnings are preserved instead of being replaced by reassuring empty-state copy.
- Regression coverage includes campaign/ad row combinations, malformed row counts, provider errors, HTTP failures, missing Google Ads configuration and warning preservation for connector empty-state classification.
- Google Analytics metric semantics are explicitly guarded for the pilot: GA `sessions` currently normalize into the generic `clicks` field, so pilot documentation and UI warnings require that those values be treated as website sessions, never paid-ad clicks or paid-media click totals.
- The pilot runbook explicitly requires recommendation-only behavior and forbids autonomous campaign, budget, bid or ad changes.
- Production database intent is confirmed from code: `DATABASE_URL`/`POSTGRES_URL` (Neon/Postgres) is preferred, while Turso is a legacy compatibility fallback.
- Database readiness diagnostics report backend intent and configuration booleans without exposing connection strings.
- Five-company pilot readiness diagnostics distinguish configuration blockers from manual launch gates, preventing a configuration-only pass from being mistaken for external-pilot approval.
- New Stripe Checkout creation is intentionally blocked by a pricing-reconciliation safety guard while the public Start / Growth / Pro model differs from the historical Starter / Growth / Scale backend and verified Stripe sandbox catalog.

## Current blockers requiring manual or external resolution

### 1. Direct Vercel connector visibility

Rechecked 2026-09-08: the connected Vercel integration still returns zero teams. GitHub simultaneously reports the latest observed `main` commit's Vercel status as successful, so this remains an integration authorization/scope problem rather than evidence that the project or deployment was deleted.

Manual action only if direct Vercel inspection is needed: reconnect/authorize the Vercel integration with access to the existing `vezmora` team/project. Do not change domains, DNS, secrets, credentials, project permissions or production settings as part of this check.

### 2. Public pricing / backend / Stripe sandbox reconciliation

The public marketing model is now **Start / Growth / Pro**, while the backend plan model and historical verified Stripe sandbox catalog still use **Starter / Growth / Scale**. New Checkout sessions are deliberately blocked until public pricing, backend plan metadata, billing tests and Stripe sandbox products/prices describe one approved model.

Do not bypass the checkout safety guard. Do not change Stripe keys, Price IDs, billing settings or payment configuration autonomously. The historical sandbox catalog is evidence of earlier test configuration only, not proof that current pilot Checkout is ready.

### 3. Google Ads API approval

The Vexmera MCC-to-client relationship is recorded as active, but Google Ads Basic Access remains an external prerequisite. Test Account Access is not sufficient for normal production-client reads.

Keep all advertising behavior read-only/recommendation-only until Basic Access and a real production read-only sync are independently verified. Do not enable external ad execution, campaign changes, budget changes or bid changes as part of pilot preparation.

### 4. Live connector verification

Automated coverage distinguishes legitimate empty accounts from provider failures without exposing secrets, but a real deployed walkthrough is still required for Google Ads and Meta. Verify that successful empty accounts show a clear empty state and provider/API failures show actionable, sanitized diagnostics.

For Google Analytics, also verify that the sessions-semantics warning is visible and that `source=google_analytics` data is not presented as paid-ad clicks, CPC/CTR input, or cross-channel paid-media click totals.

### 5. Google Analytics metric model cleanup

Google Analytics currently requests `sessions` but normalizes that value into Vexmera's generic `clicks` KPI field. Pilot safeguards now prevent that value from being interpreted as paid-ad clicks, but the long-term model should separate website sessions from advertising clicks.

Do not perform a historical data/schema migration autonomously without migration evidence and explicit compatibility coverage. Until then, treat incorrect GA click labeling or aggregation as a stop condition for GA analysis in the pilot.

### 6. Stripe sandbox end-to-end verification

After pricing reconciliation is complete, a fresh sandbox verification remains an external/manual gate where account-level Stripe state is involved. Required checks include the reconciled test catalog, signed webhook behavior, Checkout/trial flow and Customer Portal behavior.

Do not bypass the pricing guard to perform this test early.

### 7. Legal/pilot sign-off

Before inviting external pilot companies, finalize the Privacy Policy and Beta Terms with concrete legal entity/contact details, retention periods and subprocessor disclosures. Legal review remains a launch gate.

### 8. Final deployed browser QA

Perform one authenticated browser pass on the actual deployed Command Center before the first pilot. Confirm onboarding, connector empty states, connector failure states, disconnect flows, account privacy controls, GA metric semantics and recommendation-only behavior in the real deployment. Also confirm the public marketing page and `/app` render correctly in a real browser.

## Pilot safety gate

Do not start the five-company external pilot until all of the following are true:

- the active production deployment is confirmed and health can be inspected;
- `/health/beta-readiness` reports `private_beta_execution_safe=true`;
- `pilot_readiness.configuration_ready=true` with no configuration blockers;
- external execution remains disabled;
- required pilot connectors pass read-only sync checks;
- legitimate empty connector accounts and provider failures are visually distinguishable in deployed QA;
- GA sessions are not presented or aggregated as paid-ad clicks;
- public pricing, backend plan metadata, billing tests and the Stripe sandbox catalog are reconciled before any new Checkout test;
- a fresh Stripe sandbox end-to-end test passes if billing is included in the pilot;
- Privacy Policy and Beta Terms are finalized;
- authenticated browser QA passes.

## Next safe autonomous work

When direct Vercel visibility becomes available, the next low-risk checks are:

1. inspect production runtime errors and non-secret health diagnostics;
2. confirm the active deployment revision matches GitHub `main`;
3. verify execution-safety diagnostics remain safe;
4. inspect unresolved Vercel toolbar feedback;
5. update this snapshot only when evidence changes.

Until then, continue only with reversible code quality, diagnostics, tests, documentation, onboarding and beta-safety hardening that does not alter live ad execution, billing, secrets, permissions, DNS or customer data.
