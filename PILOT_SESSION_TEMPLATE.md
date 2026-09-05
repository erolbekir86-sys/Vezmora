# Vexmera private beta session template

Use one copy of this template per pilot company. Keep it free of OAuth tokens, API keys, developer tokens, passwords, payment data, or other secrets.

## Pilot profile

- Pilot number: 1 / 2 / 3 / 4 / 5
- Company label or non-sensitive alias:
- Session date:
- Primary use case:
- Connected source(s): Google Analytics / Google Ads / Meta / other
- Base currency:

## Onboarding

- Onboarding started: yes / no
- Onboarding completed: yes / no
- Time to complete:
- Steps requiring founder help:
- First confusing label or screen:
- Could the customer resume after leaving mid-onboarding: yes / no / not tested

## Connector validation

For each connected source, record only non-secret status information.

| Source | Connected | 30-day sync | Data rows present | Empty state clear | Error actionable | Secret-safe |
| --- | --- | --- | --- | --- | --- | --- |
| Google Analytics |  |  |  |  |  |  |
| Google Ads |  |  |  |  |  |  |
| Meta |  |  |  |  |  |  |

If a provider fails, record only the user-visible error category/message and non-sensitive request/reference ID where available. Never paste credentials, OAuth tokens, developer tokens, API keys, authorization headers, or raw provider payloads containing secrets.

## Recommendation quality

Capture the first recommendation the customer considered useful.

- Recommendation summary:
- Observed data used:
- User-provided context used:
- Assumptions explicitly labeled: yes / no
- Is the recommended next action concrete: yes / no
- Did the customer understand why Vexmera recommended it: yes / no
- Did the customer consider it useful: yes / no / unsure

## Safety check

- No campaign was created or published automatically: pass / fail
- No budget or bid was changed automatically: pass / fail
- No billing or payment setting changed: pass / fail
- No permission or credential setting changed: pass / fail
- Execution remained disabled: pass / fail / not independently verified
- Autopilot execution remained disabled: pass / fail / not independently verified

Any safety failure is a stop condition for the pilot until understood and fixed.

## Return-value signal

- Would the customer use Vexmera again without founder assistance: yes / no / unsure
- What task would they return for first:
- Biggest blocker to returning:
- One feature they expected but could not find:

## Session result

Choose one:

- PASS: onboarding reached a useful, understandable result with no safety failure.
- PASS WITH FRICTION: useful result reached, but founder help or confusing UX needs follow-up.
- BLOCKED: external provider/access issue prevented meaningful validation.
- FAIL: product defect or safety issue prevented a trustworthy session.

Result:

Follow-up issue(s):

## Five-pilot comparison fields

Keep these fields consistent across all five copies so the sessions can be compared directly:

- onboarding minutes
- number of founder interventions
- number of connected sources attempted
- number of sources successfully synced
- useful recommendation reached: yes / no
- recommendation grounded in observed data: yes / no / not applicable
- customer would return unassisted: yes / no / unsure
- safety failures: 0 required
