# Vexmera Private Beta pilot evidence template

Use one copy of this template per pilot company. Keep it deliberately non-sensitive: never paste credentials, OAuth tokens, API keys, payment details, full ad-account identifiers, customer secrets, or raw authorization headers into pilot evidence.

This template records evidence only. It does not authorize external ad execution, autonomous campaign changes, budget/bid changes, production billing changes, broader OAuth scopes, or any other account-owner decision.

## Pilot record

- Pilot slot: `1 / 2 / 3 / 4 / 5`
- Company reference: `non-sensitive short name or internal alias`
- Test date (UTC):
- Deployed commit SHA:
- Environment: `production / preview`
- Tester:
- Browser/device:
- Outcome: `PASS / BLOCKED / FAIL`

Do not record customer passwords, tokens, payment information, secret environment values, or screenshots containing them.

## 1. Safety preflight

Record boolean/status evidence only.

- [ ] `/health/beta-readiness` reachable
- [ ] `private_beta_execution_safe = true`
- [ ] `external_execution_enabled = false`
- [ ] `autopilot_execution_enabled = false`
- [ ] `meta_execution_scope_enabled = false`
- [ ] `dev_show_tokens_enabled = false`
- [ ] Repository/live pilot preflight completed against the same deployed revision
- [ ] No configuration blocker reported
- [ ] Remaining manual gates are explicitly treated as manual

Evidence note:

> 

If any execution-safety value is unsafe, mark this pilot `BLOCKED` and stop. Do not change runtime flags to make the checklist pass.

## 2. Account and session path

- [ ] Signup or login succeeds
- [ ] Authenticated refresh preserves the expected session
- [ ] Logout invalidates the session
- [ ] Returning to an authenticated route after logout does not restore protected state
- [ ] Password-reset flow is clear if exercised
- [ ] No token, password, internal secret, or sensitive backend detail appears in user-visible errors

Evidence note:

> 

## 3. Workspace and tenant isolation

- [ ] Correct workspace is shown after login
- [ ] Workspace switching shows only expected data
- [ ] No other pilot company's information is visible
- [ ] Unauthorized workspace access is rejected
- [ ] Empty workspace state is distinguishable from a failed data request

Evidence note:

> 

Any suspected cross-tenant exposure is a hard stop condition.

## 4. Google connector read-only path

Mark `N/A` if Google is not included for this company.

- [ ] OAuth starts from the expected Vexmera screen
- [ ] Callback returns to the expected Vexmera route
- [ ] Connected state is clear
- [ ] Requested access remains read-only for the Private Beta use case
- [ ] Read-only diagnostic/sync succeeds when the external account has data
- [ ] Valid zero-row data is rendered as an empty state rather than an error
- [ ] API/auth failure is rendered as a failure rather than fake zero data
- [ ] Disconnect removes the Vexmera connection cleanly

Evidence note:

> 

Do not paste Google refresh/access tokens, developer tokens, client secrets, login-customer identifiers, or full account identifiers here.

## 5. Meta connector read-only path

Mark `N/A` if Meta is not included for this company.

- [ ] OAuth starts from the expected Vexmera screen
- [ ] Callback returns to the expected Vexmera route
- [ ] Connected state is clear
- [ ] No unexpected write/execution scope is requested
- [ ] Read-only diagnostic/sync succeeds when data is available
- [ ] Valid zero-row data is rendered as an empty state rather than an error
- [ ] API/auth failure is rendered as a failure rather than fake zero data
- [ ] Disconnect removes the Vexmera connection cleanly

Evidence note:

> 

Do not broaden scopes to make pilot onboarding pass.

## 6. Demo-versus-live integrity

- [ ] Live-data claims appear only when a live source is actually connected
- [ ] Demo/sample data is clearly distinguishable from connected data
- [ ] Recommendations remain proposals only
- [ ] No control implies that Vexmera has executed an external ad change
- [ ] Google Analytics sessions are not presented as paid-ad clicks
- [ ] Cross-channel paid-media totals do not silently combine Google Analytics sessions with Ads clicks

Evidence note:

> 

## 7. Frontend resilience and empty states

Exercise at least one real empty state and, where safely reproducible, one failed read.

- [ ] Initial/loading state is understandable
- [ ] Valid empty state tells the user what happened and what to do next
- [ ] Failed read is visibly different from valid zero data
- [ ] Retry/reload path is understandable
- [ ] No raw stack trace, secret, token, or internal filesystem path appears
- [ ] Core navigation still works after a failed read
- [ ] Mobile/basic narrow viewport smoke check completed

Evidence note:

> 

## 8. Privacy controls

- [ ] Connector disconnect works for the tested source
- [ ] Synced-history deletion is understandable where offered
- [ ] Account-deletion preview clearly reports blockers
- [ ] Destructive account deletion, if tested, uses a dedicated test account rather than a real pilot company
- [ ] Readiness/privacy diagnostics expose status only and not secret values

Evidence note:

> 

## 9. Billing sandbox

Mark `BLOCKED` or `N/A` until pricing/catalog reconciliation is explicitly complete.

- [ ] Checkout safety gate has not been bypassed
- [ ] Stripe test mode confirmed before any sandbox transaction
- [ ] Reconciled sandbox plan/catalog matches the intended product model
- [ ] Test checkout succeeds through the normal guarded path, if enabled
- [ ] Test webhook state is reflected correctly
- [ ] No live charge is attempted

Evidence note:

> 

Never record card details, webhook secrets, Stripe API keys, customer payment data, or bank information here.

## 10. Security/header smoke check

For the deployed build:

- [ ] CSP includes the expected Private Beta hardening
- [ ] Clickjacking protection is present
- [ ] `X-Content-Type-Options: nosniff` is present
- [ ] Referrer policy is present
- [ ] Browser permissions not used by Vexmera remain disabled by policy
- [ ] Authentication cookie is `HttpOnly`; secure transport behavior is correct for the deployment

Evidence note:

> 

## 11. Product feedback

Keep feedback product-focused and non-sensitive.

- Onboarding friction:
- Confusing wording/empty state:
- Missing expected metric:
- Recommendation clarity/usefulness:
- Trust concern:
- Privacy/disconnect concern:
- Top requested improvement:

## 12. Stop-condition review

Mark every item checked before calling the pilot record complete.

- [ ] No execution-safety regression observed
- [ ] No cross-tenant exposure observed
- [ ] No secret/token exposure observed
- [ ] No unexpectedly broad connector scope observed
- [ ] No live billing reached unexpectedly
- [ ] No API failure misrepresented as valid empty data
- [ ] No Google Analytics session metric presented as paid-ad clicks
- [ ] No unresolved auth/session integrity problem observed

If any item cannot be checked, set the overall outcome to `BLOCKED` or `FAIL` and record the issue without sensitive data.

## 13. Final result

- Result: `PASS / BLOCKED / FAIL`
- Blocking issue reference, if any:
- Follow-up owner:
- Retest required: `yes / no`
- Retest commit SHA, if applicable:

Summary:

> 

A `PASS` in this document means only that the intended Private Beta read-only pilot path passed the recorded checks for this company and deployed revision. It does not authorize write scopes, external campaign execution, autonomous changes, production billing changes, or broader rollout.
