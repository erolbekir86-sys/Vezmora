# Vexmera pilot company evidence template

Use one copy of this template per pilot company. Keep the company reference generic if the repository is visible to people who do not need the customer's identity.

Do **not** paste credentials, OAuth tokens, ad-account secrets, payment details, personal data, raw customer exports, or sensitive screenshots into this file.

## Pilot reference

- Company reference: 
- Pilot slot: 1 / 2 / 3 / 4 / 5
- Date started: 
- Tester: 
- Deployed commit SHA: 
- Environment: production / preview

## Safety preflight

Record only pass/fail and non-sensitive notes.

- [ ] `/health/beta-readiness` checked
- [ ] `private_beta_execution_safe: true`
- [ ] `external_execution_enabled: false`
- [ ] `autopilot_execution_enabled: false`
- [ ] `meta_execution_scope_enabled: false`
- [ ] `dev_show_tokens_enabled: false`
- [ ] No unexpected write scope requested by a connector
- [ ] No live billing path entered

Result: PASS / BLOCKED

Non-sensitive note:

## Account and first-session evidence

- [ ] Signup/login succeeds
- [ ] Verification/reset flow works if exercised
- [ ] Command Center renders without blank or permanently hidden sections
- [ ] Overview opens
- [ ] Connections opens
- [ ] Insights opens
- [ ] Settings opens
- [ ] Basic mobile viewport smoke check completed

Result: PASS / BLOCKED

Observed friction, wording issue, or visual defect:

## Google Ads connector

Mark N/A if this company is not testing Google Ads.

- [ ] OAuth starts from the expected Vexmera route
- [ ] Redirect returns to the expected Vexmera route
- [ ] Connected state is understandable
- [ ] Read-only data is retrieved when access exists
- [ ] Valid zero-row data is presented as an empty state
- [ ] Authentication/API failure is presented as an error rather than empty data
- [ ] Disconnect works cleanly
- [ ] No external execution capability became available

Result: PASS / BLOCKED / N/A

Non-sensitive note:

## Meta Ads connector

Mark N/A if this company is not testing Meta Ads.

- [ ] OAuth starts from the expected Vexmera route
- [ ] Redirect returns to the expected Vexmera route
- [ ] Connected state is understandable
- [ ] Read-only data is retrieved when access exists
- [ ] Valid zero-row data is presented as an empty state
- [ ] Authentication/API failure is presented as an error rather than empty data
- [ ] Disconnect works cleanly
- [ ] No external execution capability became available

Result: PASS / BLOCKED / N/A

Non-sensitive note:

## Product-value validation

- [ ] Connected-source status is accurate
- [ ] Demo data and live connected data are clearly distinguishable
- [ ] No live-data claim appears for an unconnected source
- [ ] Recommendations are proposals only
- [ ] Any execution action remains unavailable or locked
- [ ] User can identify a sensible next step without staff explanation

Result: PASS / BLOCKED

Most useful insight/recommendation observed, paraphrased without customer-sensitive data:

## Privacy and disconnect

- [ ] Disconnect behavior exercised successfully
- [ ] Scoped history/deletion behavior checked where applicable
- [ ] Account-deletion blockers are understandable where applicable
- [ ] No token/secret values observed in UI, diagnostics, logs shown to the tester, or error output

Result: PASS / BLOCKED / PARTIAL

Non-sensitive note:

## Billing sandbox

Mark N/A if billing is not part of this pilot session.

- [ ] Stripe test mode confirmed
- [ ] Sandbox catalog confirmed
- [ ] Test checkout completed
- [ ] Test webhook state reflected correctly
- [ ] No live charge attempted

Result: PASS / BLOCKED / N/A

## Feedback summary

- Onboarding friction:
- Confusing wording or empty state:
- Missing expected metric:
- Recommendation clarity/usefulness:
- Trust concern:
- Disconnect/privacy concern:
- Top requested improvement:

## Blockers found

List only reproducible, non-sensitive symptoms and the affected route/feature. Do not include secrets or raw customer data.

1. 

## Final company outcome

- Overall status: NOT STARTED / IN PROGRESS / PASS / BLOCKED
- Safe to continue pilot: YES / NO
- Follow-up issue/commit references:
- Date closed:

A company should not be marked PASS while any cross-tenant, secret-exposure, execution-safety, unexpected write-scope, transport-safety, or live-billing issue remains unresolved.
