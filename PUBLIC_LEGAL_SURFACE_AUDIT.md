# Vexmera public legal surface audit

Last verified: 2026-09-15

## Live production findings

- `https://vexmera.com/privacy` is reachable and presents a Swedish privacy policy with Vexmera branding and Google user-data handling information.
- `https://vexmera.com/terms` is reachable and presents an English Terms of Service page.
- Both routes expose canonical URLs on the production domain.
- `https://vexmera.com/app` is reachable and presents the Vexmera application surface; authenticated browser behavior still requires the manual QA gate in `FINAL_MANUAL_QA.md`.

## Consistency finding

The public legal surfaces currently use different languages: Privacy is Swedish and Terms is English. This is not by itself a runtime defect, but the intended legal-language strategy should be explicit before external pilot onboarding.

No final legal translation should be published solely for visual consistency without review of substantive meaning.

## Release interpretation

Public route availability is green. Legal-content approval is still an owner/legal gate and must not be inferred from route availability.
