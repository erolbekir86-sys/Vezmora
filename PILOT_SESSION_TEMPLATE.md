# Vexmera private beta session template

Use one copy of this template per pilot company. Keep it free of OAuth tokens, API keys, developer tokens, passwords, payment data, or other secrets.

## Pre-session go / no-go

Complete this before the customer joins. Do not use the pilot session itself to discover a known access, legal, or deployment blocker.

- Production deployment healthy: yes / no
- Privacy Policy reviewed, finalized and published for the pilot: yes / no
- Beta Terms reviewed, finalized and published for the pilot: yes / no
- Execution-off beta safety controls independently verified: yes / no
- At least one customer-used source is expected to be testable today: yes / no
- Google Ads selected for this pilot: yes / no
- If Google Ads is selected, required API access and manager/client relationship are active: yes / no / not applicable
- Customer has the normal provider-side access needed to authorize the selected source(s): yes / no / unknown

Decision:

- GO: all required legal/safety checks pass and at least one relevant source is expected to be testable.
- RESCHEDULE: a known external access, legal, or deployment blocker would prevent a meaningful session.
- GO WITHOUT BLOCKED SOURCE: another relevant source can still produce a meaningful pilot result; record the blocked source separately and do not treat it as a product failure.

Pre-session decision:

Known blocker(s), using non-secret wording only:

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

If the 30-day sync succeeds and the source has sufficient data, optionally verify the 7-day and 90-day windows as a consistency check. Do not turn a provider/account limitation into a product failure when the source legitimately lacks history for the requested period.

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
