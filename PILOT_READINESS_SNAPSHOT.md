# Vexmera private beta readiness snapshot

Last reviewed: 2026-11-08

This is the canonical non-secret operational snapshot for the five-company read-only Private Beta.

## 2026-11-08 verification

- Production revision `89d4cb4f6acf75c91b04cea2277ac5918dae579c` was verified against Vercel production deployment `dpl_23Pj44uKM5rVGp2xZEaogFrmCCYE` and the exact revision reported by `/health/runtime`. This is dated evidence, not a permanent claim about the latest release.
- Revision-pinned public runtime preflight and public legal-page discoverability checks passed. These prove deployment identity, execution/transport safety and public page availability, not live provider access or legal approval.
- GitHub Actions run `42398112770` for this exact revision completed successfully: 771 tests passed. Its required 390×844 authenticated Chromium check is automated, synthetic/local evidence; it is not a fresh production customer walkthrough.
- A public read-only production smoke check passed 12 route/authorization/error expectations and fetched 26 referenced static assets successfully. Protected reads returned 401 without a session, and production docs/missing-page checks returned 404.
- Authenticated production navigation and fresh provider sync remain unverified in this review. Do not mark those gates passed based on earlier dated reports or synthetic CI.
- Shopify and LinkedIn production OAuth key sets remain absent in the non-decrypted key inventory; Instagram key presence alone does not prove external access. No credential values were retrieved.
- The marketing footer contact is aligned with the already-published Privacy/Terms contact in this change. Legal links now have real fallback destinations and the Cookies link uses the existing consent-settings handler. Ownership/monitoring of the contact address remains an owner confirmation.
- Use `docs/PILOT_TEST_PLAN_2026-11-08.md` for the prepared pilot plan. Operator decisions, legal facts and actual company participation still require current evidence.
- Billing is conditional in the company matrix for a free/read-only pilot. Application billing guards are unchanged, and a matching sandbox catalog, reviewed portal configuration and complete return trip remain required before paid self-service.

## 2026-11-07 review

- Production baseline: `68b3f15ed7387a265c17afffcd86ad070d209737`, founder-portrait PR #285. Vercel deployment `dpl_FESmUdszNABkfcCUF1vsAGGBtbcx` is `READY` and mainline CI succeeded.
- Revision-pinned public runtime preflight against `https://vexmera.com` passed. Production reports the exact baseline above; execution, Autopilot execution, Meta execution scope and token display are disabled.
- Public home, Privacy and Terms passed the GET-only discoverability preflight. This verifies availability and links, not legal approval.
- Vercel runtime error clusters returned no errors for the seven-day window checked on 2026-11-07. This does not establish that every provider path was exercised.
- The production environment key inventory still lacks `SHOPIFY_CLIENT_ID`, `SHOPIFY_CLIENT_SECRET`, `SHOPIFY_REDIRECT_URI`, `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET` and `LINKEDIN_REDIRECT_URI`. `INSTAGRAM_REDIRECT_URI` exists. Secret values were not read; no provider approval is inferred from key presence.
- The production public homepage and invite-only login page were checked in the browser. The homepage's visual enhancement incorrectly re-enabled annual billing, despite the monthly-only checkout model. This review fixes the enhancement and the click handler.
- Company-profile writes now capture workspace/form values at edit time and serialize requests. Switching company waits for the last save and reloads the active view in a fresh document. Failed saves block the switch and preserve the latest edit for retry; restored workspace selections are validated against authenticated memberships.
- The app's first health render now understands the minimal public health response. Instagram media and Shopify order/revenue telemetry now count toward persisted sync status.
- `uv.lock` records the newly resolved dependency graph, Python 3.12 is pinned, and CI installs with `uv sync --locked --extra dev` using uv 0.13.5. Vercel consumes the committed Python lockfile. Dependency compatibility, the local non-browser suite, Python compilation and all frontend JavaScript syntax checks are required before release; GitHub CI also runs the existing authenticated 390×844 browser gate.
- Post-release production revision verification is required for this review's commit. Do not confuse the baseline checks above with evidence for the new release.
- No fresh authenticated external-company/provider/Stripe walkthrough was completed in this review. Existing dated provider and sandbox evidence below remains historical.

## Release baseline checked before the 2026-10-13 update

- Production `main` at the start of the review: `cb73e29c49831da0fa4a0fa04ad3dcd690c5769b`
- Production domain: `https://vexmera.com`
- Vercel production deployment for the release is `READY`.
- `/health/runtime` reported that baseline revision at the initial check. The follow-up release deployed as `4e37beed2090974bf98033dbf27fb7fe22e32043` and passed the same revision-pinned runtime check.
- `/health/beta-readiness` reports `private_beta_execution_safe=true` and `production_transport_safe=true`.
- External marketing execution, Autopilot execution and Meta execution scope remain disabled.
- Vercel grouped runtime errors returned no errors for the seven-day window checked 2026-10-13.

## 2026-10-13 beta rerun

- Public runtime checks against `https://vexmera.com` passed with the exact production revision above. External execution, Autopilot execution, Meta execution scope and developer token display all reported disabled.
- Public home, Privacy and Terms passed the GET-only discoverability check. This confirms availability and links, not legal approval of their content.
- Vercel production environment key inventory has `INSTAGRAM_REDIRECT_URI`; it has no `SHOPIFY_CLIENT_ID`, `SHOPIFY_CLIENT_SECRET`, `SHOPIFY_REDIRECT_URI`, `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET` or `LINKEDIN_REDIRECT_URI`. Values were not read. Those two OAuth connections are therefore not ready for live pilot businesses.
- The Instagram redirect alone does not establish Meta app publication, permissions/app review or successful external account authorization. Verify that with a real permitted pilot account before promising Instagram data.
- The runtime preflight is now executable with `python -m scripts.public_runtime_preflight --base-url https://vexmera.com --expected-revision <production-sha>` and returns a non-zero exit status on a failed check.
- Current automated targeted beta checks passed locally. A fresh authenticated external-business walkthrough and real provider checks were not completed in this rerun.

## Verified healthy

### Product / browser

- Authenticated production desktop QA is complete with a synthetic account.
- Permanent mobile Chromium QA runs at exactly 390×844 and covers authenticated navigation, onboarding and account-privacy UI.
- Registration/login, onboarding, workspace routing, billing reads, account deletion preview, connector states and recommendation-only execution have regression/browser coverage.
- Public marketing, app, Privacy and Terms routes are live over HTTPS.

### Marketing connectors

- Google Ads production read-only sync has returned real campaign rows.
- Google Analytics has returned real rows and GA sessions are separated from paid-ad click semantics.
- Meta read-only sync distinguishes legitimate zero-data from provider/auth failures.
- Instagram and Shopify read-only connector paths are implemented.
- LinkedIn Ads read-only OAuth/reporting support is implemented and deployed with only `r_ads` and `r_ads_reporting`. Live LinkedIn customer sync remains provider-approval/configuration dependent.

### Stripe sandbox

Direct Stripe sandbox verification on 2026-09-24 confirms:

- active monthly Start / Growth / Pro prices at 995 / 1,495 / 2,995 SEK;
- all three prices carry pricing version `2026-09-start-growth-pro`;
- active default test-mode Billing Portal configuration exists;
- completed test Checkout evidence exists;
- test customers and subscriptions exist, including dedicated Vexmera billing/Portal QA records;
- signed webhook/database projection evidence is already recorded in the canonical blocker log;
- live-mode customer billing remains out of scope for the read-only pilot.

The only remaining Portal item is a manual external browser round-trip from Vexmera to Stripe-hosted Customer Portal and back. It is not a blocker for a free/read-only five-company Private Beta. It is required before customer-facing paid self-service is enabled.

## Technical blockers for five-company read-only Private Beta

No new code-level blocker was identified by the public runtime checks. Onboard only invited businesses whose requested read-only connectors can be verified individually. Shopify and LinkedIn cannot complete OAuth in the current production environment; Instagram external access remains unverified. The machine checks alone do not authorize onboarding.

## Remaining owner/legal gates

These cannot be inferred or invented by engineering:

- final legal entity name;
- organisation/registration number if applicable;
- registered/postal address where required;
- one verified public privacy/support contact;
- approval of final longer-lived retention commitments;
- account-specific DPA/transfer review where required;
- governing law / venue approval;
- liability clause / cap approval;
- VAT/tax treatment before live paid launch;
- qualified legal review of final Privacy Policy, Beta Terms and any required DPA.

## Not pilot blockers

- LinkedIn Advertising API approval, unless a pilot specifically requires LinkedIn live data.
- Google Basic Access upgrade while current Explorer access remains sufficient.
- live advertising execution or campaign mutation.
- live paid billing when the pilot is explicitly free/read-only.

## Current recommendation

Run an invited, free/read-only pilot only after legal/contact details are approved and each company's onboarding and intended connector are verified. Keep live billing and external campaign mutation disabled. Use `FIVE_COMPANY_PILOT_RUNBOOK.md` for per-company sign-off.
