# Frontend/browser risk audit — 2026-09-15

Scope: Private Beta customer-facing risks that can cause stale, empty or misleading UI state, plus authenticated browser gates that static/code evidence cannot replace.

## Verified protections already present

- Connector load failures are surfaced as errors rather than silently treated as empty data.
- Dashboard KPI read failures are guarded so stale/numeric values are replaced by unavailable/error state rather than presented as healthy current data.
- Notification/signal read failures are guarded so the UI does not present an empty/healthy signal state when verification failed.
- Company-profile read failures protect saved business context from being overwritten by an apparently empty form.
- Onboarding save/read behavior has fail-closed guard coverage.
- Google/Meta state handling distinguishes unsynced, healthy data, legitimate zero-data, warning and provider/auth error states.
- Auth/session/capability flows have bounded input and retention/security regression coverage.
- Mobile touch targets, reduced-motion handling and keyboard/screen-reader semantics are covered by existing implementation/tests.
- Customer Portal creation is server-side, owner/admin protected and fail-closed when the reviewed portal configuration or canonical return origin is unavailable.

## Residual browser-only risks

These cannot honestly be closed by code inspection alone:

1. Responsive layout at real mobile viewport widths, including navigation, forms, tables and modals.
2. Browser history/back/refresh behavior after onboarding, Checkout return and Customer Portal return.
3. Focus management and visual error-state placement in the fully rendered authenticated Command Center.
4. Third-party redirect behavior through Stripe/Google/Meta in a real browser session.
5. Cross-page persistence of current workspace and connector state after reload.
6. Account-deletion preview and destructive confirmation UX in a real authenticated session.

## Customer Portal-specific assessment

Code-level path is strong:
- route is POST-only and requires owner/admin role;
- an attached Stripe customer is required;
- explicit `STRIPE_BILLING_PORTAL_CONFIGURATION_ID` is required;
- production return origin must be a plain HTTPS origin;
- new regression coverage pins production return to `https://vexmera.com/?view=team`.

Remaining browser gate: open the portal using the real test workspace, return to Vexmera, reload, and confirm billing/team UI remains consistent.

## Conclusion

No additional frontend code change is justified from the current static audit beyond the added Customer Portal production-return regression case. The remaining orange browser work is evidence collection, not a known code defect. Do not mark it green until an authenticated desktop/mobile walkthrough succeeds.
