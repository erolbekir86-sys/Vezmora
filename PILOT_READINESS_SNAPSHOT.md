# Vexmera private beta readiness snapshot

Last reviewed: 2026-09-05

This file is a non-secret operational snapshot for the five-company private beta. It records only evidence that can be safely verified without changing credentials, billing, permissions, domains, DNS, or live advertising settings.

## Verified healthy

- GitHub repository is reachable and the default branch is `main`.
- Latest observed GitHub Actions run for `Vexmera CI` completed successfully on commit `36060f67f28b39ed020bd54c565249a765cb1e21`.
- The Python package identifies the product as `vexmera` version `0.6.1`.
- CI/test coverage includes deployment, execution safety, connector empty states, privacy controls, analytics consent, Google Ads diagnostics, billing alignment and beta readiness.
- The pilot runbook explicitly requires recommendation-only behavior and forbids autonomous campaign, budget, bid or ad changes.

## Current blockers requiring manual or external resolution

### 1. Vercel project visibility mismatch

The connected Vercel account exposes the team `Vezmora`, but that team currently returns no projects through the Vercel connection. Direct lookup of project slugs `vezmora` and `vexmera` in that team returns 404.

This conflicts with `DEPLOY_CHECKLIST.md`, which records earlier successful Vercel deployment work. Treat this as an account/team visibility or connection-scope issue until proven otherwise. Do not change domains, DNS, secrets, credentials or permissions to troubleshoot it.

Manual check: in Vercel, confirm which account/team owns the active Vexmera deployment and that the connected Vercel integration has access to that project.

### 2. Google Ads manager link and API approval

`DEPLOY_CHECKLIST.md` still records two external prerequisites:

- accept the pending manager-account link request for Google Ads account `638-343-6270`;
- receive Google Ads API Basic Access approval.

Do not enable ad execution while these remain unresolved. After linking is active, configure `GOOGLE_ADS_LOGIN_CUSTOMER_ID` only if required and verify read-only campaign sync first.

### 3. Stripe sandbox deployment reconciliation

The application and test catalog are prepared, but deployment reconciliation remains incomplete in `DEPLOY_CHECKLIST.md`:

- confirm the Vercel Stripe price variables reference the verified test prices;
- confirm the configured Stripe secret key belongs to the same test account;
- create/reconcile the test webhook endpoint;
- verify `stripe_sandbox_ready=true`;
- run an end-to-end sandbox Checkout, trial, signed webhook and Customer Portal test.

These steps involve deployment secrets or external account configuration and therefore require manual handling.

### 4. Legal/pilot sign-off

Before inviting external pilot companies, finalize the Privacy Policy and Beta Terms with concrete legal entity/contact details, retention periods and subprocessor disclosures. Legal review remains a launch gate.

### 5. Final deployed browser QA

Perform one authenticated browser pass on the actual deployed Command Center before the first pilot. Confirm onboarding, connector empty states, disconnect flows, account privacy controls and recommendation-only behavior in the real deployment.

## Pilot safety gate

Do not start the five-company external pilot until all of the following are true:

- the active Vercel project is visible/confirmed and production health can be inspected;
- external execution remains disabled;
- required pilot connectors pass read-only sync checks;
- Stripe sandbox readiness passes if billing is included in the pilot;
- Privacy Policy and Beta Terms are finalized;
- authenticated browser QA passes.

## Next safe autonomous work

Once Vercel project visibility is restored, the next low-risk automated checks should be:

1. inspect production runtime errors and health diagnostics;
2. compare the active deployment commit with GitHub `main`;
3. verify no execution-safety regressions are present;
4. inspect unresolved Vercel toolbar feedback;
5. update this snapshot only when evidence changes.
