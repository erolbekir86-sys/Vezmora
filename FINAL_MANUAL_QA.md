# Vexmera final manual QA

Last updated: 2026-09-15

Purpose: the shortest evidence-producing walkthrough required before the five-company Private Beta. This checklist intentionally covers only steps that automated code/CI and public read-only checks cannot prove.

## Desktop authenticated walkthrough

1. Open `https://vexmera.com/app` in a normal desktop browser.
2. Register a disposable QA account or log in with the intended pilot test account.
3. Confirm login lands in the expected authenticated application state and does not expose another workspace.
4. Complete or review onboarding. Confirm refresh does not lose saved company context.
5. Open Core, Pulse, Launch, Brief, Queue, Autopilot, Competitors, Connections, Insights, Team and Brand.
6. Confirm API/provider failures show a clear error or unavailable state rather than stale or zero-looking data.
7. Confirm legitimate empty connector data is visibly different from an authentication/provider failure.
8. Confirm Autopilot remains recommendation-only and no live external execution action is available.
9. Open account/privacy controls and request the deletion preview only. Do not delete the account.
10. Log out, refresh, confirm authenticated data is no longer available, then log back in.

## Customer Portal return check

Prerequisites already verified elsewhere: test Checkout complete, active test subscription, signed webhook projection, active Billing Portal configuration and production return-origin regression coverage.

1. From the authenticated billing UI, open Customer Portal.
2. Confirm the portal belongs to the expected Vexmera test customer and uses test mode.
3. Do not make a destructive billing change unless specifically intended for the test account.
4. Use the portal return control.
5. Confirm the browser returns to `https://vexmera.com/?view=team` or the intended application route.
6. Reload Vexmera and confirm plan/billing state still renders correctly.

## Mobile viewport pass

Run at an iPhone-class width, approximately 390 px.

- login/registration controls remain usable;
- left navigation does not cover content;
- primary navigation remains reachable;
- forms do not overflow horizontally;
- tables/cards remain understandable;
- dialogs/modals fit the viewport and can be closed;
- touch targets remain comfortably tappable;
- Cookie Settings and account/privacy controls remain reachable;
- billing buttons do not clip or overlap;
- no horizontal page scroll caused by core application layout.

## Pass criteria

Mark this gate green only when desktop, Customer Portal return and mobile viewport pass without a material blocker. Record screenshots only if they contain no secrets, OAuth tokens or sensitive customer data.
