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

Run the consolidated repository + deployed read-only gate from the release candidate you intend to pilot:

```bash
python scripts/pilot_go_no_go.py --base-url https://vexmera.com
```

This combines configuration checks with GET-only checks for public execution-lock evidence, production deployment identity and legal-page discoverability. It sends no credentials and performs no mutations. The public runtime check verifies Vercel production identity and that a deployment revision is present; database/provider access still requires the separate manual evidence below.

If production is temporarily unavailable and you only need a local configuration snapshot, `python scripts/pilot_preflight.py` remains useful, but it is **not** a substitute for the consolidated deployed gate before onboarding a real pilot company.

Treat `status: blocked`, any reported blocker, or a non-zero exit code as a stop condition. An exit code of zero means only that machine-checkable checks are clear; it does **not** mean the pilot is approved or ready while `manual_verification_required` is true or manual gates remain.

Do not onboard a pilot company if any of those conditions fail.

Never enable external ad execution, autonomous campaign changes, budget or bid changes, live billing changes, or broader ad-platform write scopes as part of this pilot.

## Global gates before company 1

These remain manual gates even when configuration checks are green:

- [ ] Final authenticated browser QA on the deployed application
- [ ] Privacy Policy and Beta Terms reviewed and ready for the intended business pilot
- [ ] Google Ads external approval / manager linking completed if required for read access
- [ ] Public pricing, backend plans and Stripe sandbox catalog reconciled to the same current model
- [ ] Fresh Stripe sandbox end-to-end test completed **only after** pricing reconciliation is complete and the checkout safety gate is intentionally open
- [ ] Production transport check is green
- [ ] Core internal-secret configuration check is green (boolean only; never copy secret values into pilot evidence)
- [ ] Remote database configuration check is green
- [ ] Transactional email configuration check is green
- [ ] Google OAuth configuration check is green
- [ ] Meta OAuth configuration check is green if Meta is included in the pilot
- [ ] Production runtime/log observability has been reviewed when the Vercel project is visible to operator tooling

Do not bypass the pricing-migration checkout guard to satisfy a pilot checklist. The historical Starter / Growth / Scale sandbox catalog is evidence of earlier test configuration, not the current pilot billing target.

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
- [ ] Run `python scripts/pilot_go_no_go.py --base-url https://vexmera.com` against the same deployed revision and confirm no blocker is reported
- [ ] Confirm the reported deployment revision matches the release candidate intended for the pilot
- [ ] Record remaining manual gates as unresolved until current evidence exists; never interpret `ok: true` as pilot approval
- [ ] Confirm execution remains locked
- [ ] Confirm the company understands the pilot is analysis/recommendation only
- [ ] Confirm the correct company/user account is being onboarded
- [ ] Confirm no secrets will be copied into support notes or screenshots

### 2. Account creation and first session

- [ ] Signup/login succeeds
- [ ] Verification/password-reset flow works if used
- [ ] When password reset is exercised, requesting a newer reset link makes the older outstanding reset link unusable
- [ ] A successful password reset invalidates previously issued authenticated sessions for that account
- [ ] Reset/invite capability URLs are not retained by browser/CDN caches and do not leak through the `Referer` header
- [ ] When a workspace invitation is resent to the same email address for the same workspace, the older outstanding invite becomes unusable while accepted invite history remains intact
- [ ] Command Center loads without blank or partially hidden sections
- [ ] Navigation to Connections, Overview, Insights and Settings works
- [ ] Mobile viewport receives a basic smoke check

Use a dedicated test account for reset/session invalidation checks. Do not disrupt an active pilot user's session merely to satisfy the checklist.

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
- [ ] Google Analytics `sessions` are treated as website sessions, not paid-ad clicks, even though the current normalized KPI schema temporarily stores that value in the generic `clicks` field
- [ ] Paid-media click totals, CPC/CTR interpretation, and cross-channel comparisons do not combine `source=google_analytics` click values with Google Ads or Meta Ads clicks during the private beta

Until the KPI schema has a dedicated sessions field, the Google Analytics sync warning is an intentional beta-safety disclosure. Do not remove, hide, or reinterpret it merely to make the pilot look cleaner.

### 5. Privacy and deletion check

At least once before the pilot is considered complete, and whenever a related code path changes:

- [ ] Connector disconnect works
- [ ] Scoped synced-history deletion works where offered
- [ ] Account-deletion flow exposes its blockers clearly
- [ ] No secret/token values are exposed by readiness diagnostics

Do not delete a real pilot company's data merely to satisfy a test. Use a dedicated test account for destructive deletion validation.

### 6. Billing sandbox check

If billing is shown during the pilot, first confirm pricing reconciliation is complete. If it is not complete, leave checkout blocked and mark the billing check `BLOCKED` or `N/A`; do not bypass the guard or reuse the historical catalog as if it were current.

Only after reconciliation:

- [ ] Stripe is in test mode
- [ ] The current reconciled sandbox catalog matches the public/backend plan model
- [ ] Test checkout succeeds through the normal guarded flow
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
- consolidated pilot go/no-go reports `blocked` or a public/live/runtime/legal blocker
- the deployed revision cannot be identified or does not match the intended release candidate
- the app shows another company's data
- authentication or tenant isolation appears incorrect
- a reset link remains valid after a newer reset link is issued for the same account
- an old authenticated session survives a successful password reset
- an older outstanding workspace invite remains valid after the same address is re-invited to the same workspace
- a connector requests unexpectedly broad/write permissions
- live billing is reached unexpectedly
- a secret or token appears in UI, logs, diagnostics, screenshots, or error output
- an API failure is misrepresented as valid empty data in a way that could mislead the user
- Google Analytics sessions are presented or used as paid-ad clicks without an explicit source distinction
- production transport is reported unsafe

Resume only after the issue is understood, fixed, tested, and redeployed.

## Pilot completion criteria

The five-company pilot is operationally complete only when:

1. all five companies can complete the intended read-only onboarding path,
2. no unresolved cross-tenant, secret-exposure, execution-safety, billing-safety, or metric-semantics issue remains,
3. empty states and connector failures are distinguishable and understandable,
4. disconnect/privacy controls have been exercised successfully,
5. final browser QA has been completed on the deployed build,
6. feedback has been converted into a prioritized post-pilot backlog.

Configuration readiness alone does not prove these criteria; the existing manual gates still apply.
