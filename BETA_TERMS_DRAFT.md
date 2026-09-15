# Vexmera Private Beta Terms — DRAFT

> **Status:** Private-beta draft aligned with verified product controls as of 2026-09-15. Contracting entity, registration number, address, verified contact, governing law/venue, liability cap, final VAT/tax treatment and final legal review remain owner/legal gates.

**Last updated:** 2026-09-15

## 1. About these beta terms
These terms are intended for invited business users participating in the Vexmera Private Beta.

Before external use, insert and verify:
- Legal entity: [TO BE ADDED]
- Registration number: [TO BE ADDED]
- Address: [TO BE ADDED]
- Contact email: [TO BE ADDED]

The pilot is intended for business customers, but final legal review must confirm whether any consumer rules could apply to the actual contracting setup.

## 2. The service
Vexmera is an AI-powered marketing platform designed to connect marketing/analytics data, explain performance and recommend next actions. Private Beta is pre-release software. Features may change, be incomplete or temporarily unavailable, and third-party APIs may restrict functionality.

## 3. Read-only advertising posture
During Private Beta, supported Google Ads and Meta Ads integrations are read-only. Production currently reports external execution disabled, Autopilot execution disabled and Meta execution scope disabled.

Vexmera must not autonomously publish ads, create or activate live campaigns, change budgets/bids/targeting, pause campaigns or otherwise mutate connected advertising accounts during this beta posture.

Vexmera may prepare recommendations, analyses, drafts and approval items. Any later execution capability requires separate product, provider, security and customer-control review.

## 4. Accounts and customer responsibilities
Users are responsible for accurate registration information, protecting login credentials, ensuring they are authorized to connect third-party accounts and data, controlling invited team access and promptly reporting suspected compromise.

Users must not attempt to access another customer's workspace, extract secrets, bypass safeguards or connect data they are not authorized to process.

## 5. Third-party services
Vexmera relies on third-party providers for hosting/runtime, database services, AI processing, billing, transactional email and connected analytics/advertising APIs. Provider availability, approval status, quotas and API changes may affect Vexmera.

A current technical provider/data-flow inventory is maintained in `SUBPROCESSOR_DATA_INVENTORY.md`. Provider legal roles may differ by activity, and third-party terms may also apply directly to the customer or user.

## 6. Customer data and data-processing roles
The customer confirms that it has the necessary rights, permissions and lawful basis to provide or connect data to Vexmera.

Where Vexmera processes personal data on behalf of a business customer, a separate Data Processing Agreement may be required. Controller/processor roles must be determined per processing activity rather than assumed globally.

## 7. AI-generated recommendations
AI-generated analysis may be incomplete, inaccurate, outdated or unsuitable for a specific business. Customers remain responsible for advertising, financial, legal and operational decisions. Vexmera should distinguish observed data from assumptions or generated recommendations where reasonably possible.

## 8. Beta limitations
Private Beta is provided for testing, evaluation and feedback. Users acknowledge that synchronization can fail or be delayed, historical provider data may be incomplete, provider approvals can constrain features, AI recommendations can be imperfect and features can change without generally available service-level commitments.

Vexmera should not be treated as the sole authoritative record for advertising, billing, accounting or regulatory information.

## 9. Acceptable use
Users must not use Vexmera to violate law or third-party rights, introduce malicious code, circumvent access/execution controls, use connected credentials without authorization, access another customer's data or deliberately misrepresent generated recommendations as independently verified fact.

## 10. Trial, subscription and billing
The product includes a 14-day trial design and Stripe subscription flows. Test-mode Stripe evidence currently verifies a completed Start-plan Checkout, an active resulting test subscription, signed billing-event projection into Vexmera and an active test-mode Billing Portal configuration.

Live paid production billing must not be represented as finally launched until live billing, tax/VAT, legal and browser-return checks are complete.

Before live paid use, final terms must match the actual production configuration for plan names/prices, billing cycle, trial eligibility, renewal, VAT/taxes, cancellation, refunds if any, failed payments and post-cancellation access.

Test-mode activity creates no production payment obligation.

## 11. Cancellation and Customer Portal
The currently verified test-mode Billing Portal configuration allows payment-method/customer-detail updates and cancellation at the end of the billing period. A full authenticated browser verification of opening Customer Portal through Vexmera and returning safely to the application remains a release gate before billing-enabled external pilot use.

Final public terms must match the live Stripe configuration actually enabled at launch.

## 12. Feedback
Vexmera may use beta feedback to improve the product without payment, provided confidential customer information is not publicly disclosed. `RETENTION_POLICY_PROPOSAL.md` currently proposes a bounded period for identifiable beta feedback, but this is not yet a public commitment until operational/legal verification is complete.

## 13. Confidentiality
Each party should protect non-public business, technical and product information received through the beta relationship and use it only for the beta except where disclosure is authorized or legally required. Final legal review should strengthen this clause if pilot customers share commercially sensitive strategy or campaign information.

## 14. Intellectual property
Vexmera and its licensors retain rights in the platform, software, branding, documentation and product design. Customers retain rights in their own data/materials, subject to permissions needed for Vexmera and its providers to operate the service under the Privacy Policy and any applicable DPA.

## 15. Disconnect, synchronized-history deletion and account deletion
These controls are intentionally separate:

- **Disconnect Google/Meta:** removes Vexmera's locally stored connector credential and saved provider/account configuration, stops future sync through that credential and attempts provider-side revocation. Previously synchronized reporting history remains.
- **Delete synchronized reporting history:** authorized owner/admins can separately remove synchronized campaign rows, imported provider KPI rows, anomalies and anomaly notifications after explicit confirmation. Manually entered KPI rows remain.
- **Delete Vexmera account:** guarded self-service flow requires password re-authentication and exact confirmation. Deletion is blocked if an owned workspace still has other members or an active attached subscription. Eligible solo-owned local workspaces/account data are deleted and memberships in other owners' workspaces are removed.

Third-party billing, accounting, security, anti-fraud or compliance records may remain where retention is legally or operationally required.

## 16. Retention
Verified short-lived capability retention currently includes 14-day sessions, 60-minute password-reset capabilities and 7-day workspace invites, with pruning/supersession controls.

Longer-lived product-data periods are being defined in `RETENTION_POLICY_PROPOSAL.md`. They must not become customer promises until engineering verifies any scheduled deletion required to meet them and legal/accounting review confirms statutory retention obligations.

## 17. Suspension and termination
Vexmera may suspend access where reasonably necessary for security, suspected abuse, provider restrictions, legal compliance or material breach. Beta customers may stop using the service at any time. If live paid subscriptions are later enabled, cancellation and post-cancellation access must follow the then-current production terms and Stripe configuration.

## 18. Security
Vexmera uses access controls, HTTPS, secure session settings, encrypted connector credential storage, CSRF/security-header protections and server-side execution locks. No system can guarantee absolute security.

## 19. Disclaimers
To the extent permitted by law, Private Beta is provided on an "as available" basis without a guarantee of uninterrupted operation, error-free output or suitability for every marketing objective. Vexmera does not guarantee revenue, conversion, acquisition or profitability outcomes.

## 20. Limitation of liability
[TO BE COMPLETED AFTER QUALIFIED LEGAL REVIEW]

Do not publish an arbitrary liability cap. The final clause should address indirect loss, lost profits, data loss, interruption and an appropriate aggregate cap while preserving liabilities that cannot lawfully be excluded.

## 21. Governing law and disputes
[TO BE COMPLETED AFTER LEGAL REVIEW]

Final terms must specify governing law, venue and any mandatory protections applicable to the final operator/customer type.

## 22. Privacy and data processing
Use is also subject to the Vexmera Privacy Policy. Where Vexmera acts as processor for business-customer personal data, a legally reviewed DPA may be required. International-transfer safeguards and final processor/subprocessor disclosures must reflect the actual production accounts/contracts.

## 23. Changes and contact
Material changes should be communicated appropriately before taking effect where required.

Contact: [TO BE ADDED BEFORE EXTERNAL USE]

## Internal review references
- `PRIVACY_POLICY_DRAFT.md`
- `RETENTION_POLICY_PROPOSAL.md`
- `SUBPROCESSOR_DATA_INVENTORY.md`
- `DATA_HANDLING.md`
- `LEGAL_REVIEW_PREP.md`
- `PRODUCTION_ENVIRONMENT.md`
- `DEPLOY_CHECKLIST.md`

Unresolved legal, tax or provider questions must remain explicit TODOs rather than being turned into customer promises.