# Vexmera five-company pilot execution matrix

Use this as the single execution sheet for the first five Private Beta companies.

## Release gate before company 1
- Production deployment is READY on latest approved `main`.
- Vexmera CI green for latest release changes.
- External ad execution remains disabled.
- Autopilot external execution remains disabled.
- Stripe remains test-mode unless a separate owner-approved live-billing launch is completed.
- Authenticated desktop/mobile smoke test completed.
- Customer Portal round-trip completed in sandbox.
- Legal operator/contact/VAT decisions filled in and public Privacy/Terms reviewed.

## Per-company matrix
| Company | Owner/contact confirmed | Workspace created | Onboarding | Google read-only | Meta read-only | Dashboard data | Core/Pulse | Empty/error states | Billing sandbox | Feedback captured | PASS/STOP |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Pilot 1 | ☐ | ☐ | ☐ | ☐/N/A | ☐/N/A | ☐ | ☐ | ☐ | ☐ | ☐ | |
| Pilot 2 | ☐ | ☐ | ☐ | ☐/N/A | ☐/N/A | ☐ | ☐ | ☐ | ☐ | ☐ | |
| Pilot 3 | ☐ | ☐ | ☐ | ☐/N/A | ☐/N/A | ☐ | ☐ | ☐ | ☐ | ☐ | |
| Pilot 4 | ☐ | ☐ | ☐ | ☐/N/A | ☐/N/A | ☐ | ☐ | ☐ | ☐ | ☐ | |
| Pilot 5 | ☐ | ☐ | ☐ | ☐/N/A | ☐/N/A | ☐ | ☐ | ☐ | ☐ | ☐ | |

## Mandatory smoke flow for each workspace
1. Log in and verify the intended workspace is selected.
2. Complete or review company profile/onboarding.
3. Open Overview, Core, Pulse, Launch, Brief, Queue, Autopilot, Konkurrenter, Anslutningar, Insikter, Team and Varumärke.
4. Confirm data-loading failures show an explicit error/unknown state, never believable zero/current data.
5. Where Google or Meta is connected, sync only read-only reporting data and compare at least one metric/date range with the source platform.
6. Confirm Queue and Autopilot messaging states that external execution is gated and disabled for the Private Beta.
7. Verify billing state is understandable. Do not start live billing during the pilot release gate.
8. Capture one short user feedback note and any blocker.

## Stop conditions
Stop onboarding additional pilot companies if any of these occur:
- cross-workspace data visibility
- OAuth token/secret exposure
- incorrect company data shown as current/verified
- external ad mutation unexpectedly becomes available
- Stripe uses live mode unexpectedly
- repeated 5xx/auth failures that prevent normal pilot use
- deletion/privacy controls behave outside their documented scope

## Pass definition
A company passes when its normal read-only marketing workflow works without a critical safety/data-integrity defect, and any known limitation is clearly represented to the user rather than silently producing misleading data.
