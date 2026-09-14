# Vexmera Private Beta — five-company pilot runbook

This runbook is the release gate for the first five external companies. It is intentionally conservative: the pilot is read-only for ad-platform execution and remains sandboxed for billing until the explicit owner-controlled launch gates are completed.

## 1. Release candidate gate

Before inviting a pilot company:

- `main` CI is green.
- No known high-severity auth, session, CSRF, secret-handling, billing-webhook, or tenant-isolation defect is open.
- External ad execution remains disabled.
- Autopilot execution remains disabled.
- Meta execution scopes remain disabled.
- Development token-display functionality remains disabled.
- Production diagnostics expose booleans/status only, never credentials, tokens, connection strings, webhook secrets, or API keys.
- The current release candidate has an immutable commit SHA recorded in the pilot log.

## 2. Authentication and session QA

For each release candidate verify:

- registration, login and logout complete successfully;
- expired/invalid sessions return a safe unauthenticated state rather than a broken app shell;
- authenticated cross-origin mutations are rejected;
- public browser auth POSTs reject cross-origin requests;
- malformed configured canonical origins fail closed;
- password-reset flows do not disclose whether an account exists beyond the intended product behavior;
- auth/OAuth callback responses do not leak sensitive query data through referrers;
- cookies use the expected production security attributes.

Do not use production credentials in screenshots, test fixtures, logs, issues, PR descriptions, or pilot notes.

## 3. Demo versus live integrity

Every user-facing surface must make its data source unambiguous.

Verify that:

- demo/sample data is visibly identified as demo/sample data;
- live connector data is never silently replaced with demo data after an error;
- disconnected connectors show a clear empty/disconnected state;
- read-only connection status is visible where a user might otherwise expect Vexmera to make campaign changes;
- recommendations are presented as recommendations, not evidence that an external change has already occurred;
- failed or stale syncs are distinguishable from genuine zero-result states.

## 4. Google Ads read-only pilot gate

For each pilot workspace:

- OAuth connection succeeds with the minimum intended scopes;
- account/customer selection resolves to the intended advertiser;
- a live read-only sync can fetch expected campaign/account data;
- connector errors are actionable and do not expose tokens;
- disconnect removes Vexmera's stored connector access according to the implemented deletion flow;
- no campaign creation, budget change, bid change, pause/resume, or other mutation is available in the pilot path.

External Google approval, Cloud-project access, and manager-account linking remain owner-controlled gates where required.

## 5. Meta read-only pilot gate

For each pilot workspace:

- OAuth connection succeeds with the minimum intended read-only access;
- the intended ad account can be selected and read;
- live read-only sync produces expected data or a clear diagnostic state;
- connector errors do not expose access tokens;
- disconnect/deletion follows the implemented privacy controls;
- execution scopes and external campaign mutation remain disabled.

Any Meta app-review or external account-permission step is an owner-controlled gate.

## 6. Stripe sandbox gate

The pilot billing path remains sandbox/test mode until a separate owner decision enables live billing.

Verify:

- Stripe key mode is test/sandbox;
- current Start/Growth/Pro price configuration is reconciled to the current pricing version;
- webhook signing secret is configured without exposing its value;
- missing/invalid webhook signatures fail safely;
- oversized webhook payloads/signature headers are rejected;
- duplicate event delivery is side-effect safe;
- workspace/customer mismatches are rejected;
- a fresh sandbox checkout reaches the correct workspace and plan;
- a fresh signed sandbox webhook updates the expected local billing projection;
- the reviewed Private Beta billing-portal configuration is explicitly selected.

Live payment activation, payout/bank details, KYC, tax/VAT configuration and final commercial billing policy are owner-controlled launch gates.

## 7. Frontend resilience and empty states

Verify the main application with these states:

- brand-new workspace with no connectors;
- Google connected, Meta disconnected;
- Meta connected, Google disconnected;
- both connectors disconnected;
- connector permission/error state;
- connector returning no campaigns/data;
- stale sync state;
- network/API failure;
- expired session;
- billing unavailable/sandbox not ready.

The user should always get a clear next action. A backend error must not turn into an empty-looking dashboard that can be mistaken for valid zero data.

## 8. Pilot company onboarding checklist

For each of the five companies record only non-secret operational metadata:

- pilot slot number (1–5);
- company/workspace display name;
- primary contact;
- release commit SHA used at onboarding;
- Google status: not requested / connected / blocked / verified read-only;
- Meta status: not requested / connected / blocked / verified read-only;
- Stripe sandbox status: not used / verified;
- onboarding completed date;
- known non-sensitive blocker summary;
- follow-up owner.

Never put tokens, API keys, passwords, webhook secrets, bank data, identity documents, or raw OAuth authorization data in the pilot log.

## 9. Stop conditions

Pause new pilot onboarding if any of the following occurs:

- suspected cross-workspace data exposure;
- auth/session bypass;
- CSRF bypass on an authenticated mutation;
- secret/token disclosure;
- unsigned Stripe webhook accepted;
- incorrect workspace billing mutation;
- live ad-platform mutation becomes reachable;
- demo data is presented as live data;
- a connector can access an account outside the intended pilot workspace/account selection.

Existing pilot access should be assessed case-by-case, with the safest default being to disable the affected feature rather than widening permissions or bypassing safeguards.

## 10. Owner-controlled gates

The following are deliberately outside autonomous release work and require Erol/account-owner action or explicit business approval:

- DNS/domain changes;
- credentials/secrets creation or rotation;
- Google/Meta external account permissions and approvals;
- KYC or identity verification;
- bank/payout details;
- live Stripe activation;
- live advertising execution;
- real budget or bid changes;
- legal acceptance or final commercial policy decisions.

Passing this runbook means the release candidate is suitable for a controlled five-company Private Beta. It does not by itself authorize a broad public launch or external advertising execution.
