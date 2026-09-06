# Vexmera five-company pilot runbook

This runbook turns the existing private-beta safety checks into a repeatable onboarding and validation process for the first five companies.

It is intentionally conservative: the pilot is for connection, read-only analysis, recommendations, onboarding quality, billing sandbox validation, and product feedback. It does **not** authorize Vexmera to execute external ad changes.

## Non-negotiable safety boundary

Before every pilot onboarding, confirm `/health/beta-readiness` reports:

- `private_beta_execution_safe: true`
- `external_execution_enabled: false`
- `autopilot_execution_enabled: false`
- `meta_execution_scope_enabled: false`
- `dev_show_tokens_enabled: false`

Do not onboard a pilot company if any of those conditions fail.

Never enable external ad execution, autonomous campaign changes, budget or bid changes, live billing changes, or broader ad-platform write scopes as part of this pilot.

## Global gates before company 1

These remain manual gates even when configuration checks are green:

- [ ] Final authenticated browser QA on the deployed application
- [ ] Privacy Policy and Beta Terms reviewed and ready for the intended business pilot
- [ ] Google Ads external approval / manager linking completed if required for read access
- [ ] Fresh Stripe sandbox end-to-end test completed
- [ ] Production transport check is green
- [ ] Remote database configuration check is green
- [ ] Transactional email configuration check is green
- [ ] Google OAuth configuration check is green
- [ ] Meta OAuth configuration check is green if Meta is included in the pilot

## Pilot roster

Use one row per company. Do not store credentials, tokens, account secrets, payment details, or sensitive customer data in this file.

| Slot | Company reference | Owner/contact confirmed | Legal accepted | Google connected | Meta connected | Read-only data verified | Empty states verified | Disconnect tested | Feedback captured | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 |  | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | Not started |
| 2 |  | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | Not started |
| 3 |  | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | Not started |
| 4 |  | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | Not started |
| 5 |  | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | Not started |

## Per-company onboarding sequence

### 1. Preflight

- [ ] Re-check `/health/beta-readiness`
- [ ] Confirm execution remains locked
- [ ] Confirm the company understands the pilot is analysis/recommendation only
- [ ] Confirm the correct company/user account is being onboarded
- [ ] Confirm no secrets will be copied into support notes or screenshots

### 2. Account creation and first session

- [ ] Signup/login succeeds
- [ ] Verification/password-reset flow works if used
- [ ] Command Center loads without blank or partially hidden sections
- [ ] Navigation to Connections, Overview, Insights and Settings works
- [ ] Mobile viewport receives a basic smoke check

### 3. Connector onboarding

For each connector included for that company:

- [ ] OAuth begins from the expected Vexmera screen
- [ ] Redirect returns to the expected Vexmera route
- [ ] User sees a clear connected state after success
- [ ] Read-only data can be retrieved when access is available
- [ ] A valid zero-row result is shown as an empty state, not as an error
- [ ] An authentication/API failure is shown as an error, not as a fake empty state
- [ ] Disconnect removes the Vexmera connection cleanly

Do not expand requested scopes merely to make onboarding pass.

### 4. Product-value check

- [ ] Overview renders the connected source state accurately
- [ ] Insights/recommendations distinguish demo data from live connected data
- [ ] No live-data claim appears when a source is not connected
- [ ] Recommendations remain proposals only
- [ ] Any action requiring external execution remains unavailable/locked
- [ ] The user can understand the next useful step without staff explanation

### 5. Privacy and deletion check

At least once before the pilot is considered complete, and whenever a related code path changes:

- [ ] Connector disconnect works
- [ ] Scoped synced-history deletion works where offered
- [ ] Account-deletion flow exposes its blockers clearly
- [ ] No secret/token values are exposed by readiness diagnostics

Do not delete a real pilot company's data merely to satisfy a test. Use a dedicated test account for destructive deletion validation.

### 6. Billing sandbox check

If billing is shown during the pilot:

- [ ] Stripe is in test mode
- [ ] Verified sandbox catalog is in use
- [ ] Test checkout succeeds
- [ ] Test webhook state is reflected correctly
- [ ] No live charge is attempted

### 7. Feedback capture

Capture only product-relevant notes:

- [ ] Onboarding friction
- [ ] Confusing wording or empty states
- [ ] Missing but expected metrics
- [ ] Recommendation clarity/usefulness
- [ ] Trust concerns
- [ ] Disconnect/privacy concerns
- [ ] Top requested improvement

Avoid copying customer credentials, tokens, ad-account secrets, payment data, or unnecessary personal data into GitHub issues or documentation.

## Stop conditions

Pause onboarding for the affected company if any of the following occurs:

- execution safety check becomes false
- the app shows another company's data
- authentication or tenant isolation appears incorrect
- a connector requests unexpectedly broad/write permissions
- live billing is reached unexpectedly
- a secret or token appears in UI, logs, diagnostics, screenshots, or error output
- an API failure is misrepresented as valid empty data in a way that could mislead the user
- production transport is reported unsafe

Resume only after the issue is understood, fixed, tested, and redeployed.

## Pilot completion criteria

The five-company pilot is operationally complete only when:

1. all five companies can complete the intended read-only onboarding path,
2. no unresolved cross-tenant, secret-exposure, execution-safety, or billing-safety issue remains,
3. empty states and connector failures are distinguishable and understandable,
4. disconnect/privacy controls have been exercised successfully,
5. final browser QA has been completed on the deployed build,
6. feedback has been converted into a prioritized post-pilot backlog.

Configuration readiness alone does not prove these criteria; the existing manual gates still apply.
