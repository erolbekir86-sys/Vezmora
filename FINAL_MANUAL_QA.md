# Vexmera final manual QA

Last updated: 2026-09-15

Purpose: the shortest evidence-producing walkthrough required before the five-company Private Beta. This checklist intentionally covers only steps that automated code/CI and production read-only checks cannot prove.

## Already verified automatically or from production

These items are no longer part of the manual browser burden:

- Unauthenticated `/app` serves the auth shell with the authenticated app shell initially hidden.
- Representative workspace read APIs return HTTP 401 without an authenticated session.
- `/app` is `noindex`, `no-store` and protected by current production security headers.
- Production runtime has no current error cluster in the latest verification window.
- Mobile CSS now includes a fail-closed guard so responsive `display:block!important` rules cannot visually unhide `#appShell` before login.
- Stripe sandbox Checkout, active subscription, signed webhook projection, local billing state, Billing Portal configuration and production return-origin regression coverage are already verified elsewhere.

## Desktop authenticated walkthrough

1. Open `https://vexmera.com/app` in a normal desktop browser and log in with the intended pilot test account.
2. Confirm login lands in the expected workspace. If the test account has access to more than one workspace, switch between them and verify data does not bleed across workspaces.
3. Complete or review onboarding. Confirm refresh does not lose saved company context.
4. Open Core, Pulse, Launch, Brief, Queue, Autopilot, Konkurrenter, Anslutningar, Insikter, Team and Varumärke.
5. Trigger or observe at least one safe read/error condition and confirm a clear unavailable/error state is shown rather than believable zero/current data.
6. Confirm Autopilot remains recommendation-only and no live external execution action is available.
7. Open account/privacy controls and request the deletion preview only. Do not delete the account.
8. Log out, refresh, confirm authenticated content is not available, then log back in.

## Customer Portal return check

Only the browser round-trip remains manual.

1. From the authenticated billing UI, open Customer Portal.
2. Confirm the portal belongs to the expected Vexmera test customer and is test mode.
3. Do not make a destructive billing change unless specifically intended for the test account.
4. Use the portal return control.
5. Confirm the browser returns to Vexmera and the Team/Billing view is reachable as intended.
6. Reload Vexmera and confirm plan/billing state still renders correctly.

## Mobile viewport pass

Run at an iPhone-class width, approximately 390 px. The pre-login app-shell visibility risk is already regression-covered, so the remaining mobile pass is interaction/layout evidence only.

- login/registration controls remain usable;
- mobile menu opens/closes and does not cover content incorrectly;
- primary navigation remains reachable;
- forms do not overflow horizontally;
- tables/cards remain understandable;
- dialogs/modals fit the viewport and can be closed;
- touch targets remain comfortably tappable;
- Cookie Settings and account/privacy controls remain reachable;
- billing buttons do not clip or overlap;
- no horizontal page scroll caused by core application layout.

## Pass criteria

Mark the final manual gate green only when the authenticated desktop walkthrough, Customer Portal return and mobile interaction pass complete without a material blocker. Record screenshots only if they contain no secrets, OAuth tokens or sensitive customer data.
