# Vexmera Privacy Policy — DRAFT

> **Status:** Private-beta draft. The technical/data-handling sections below have been aligned with the current implementation as of 2026-09-15. Legal entity, registration number, postal address, verified privacy contact, final retention commitments, VAT/tax position and final legal review remain owner/legal gates.

**Last updated:** 2026-09-15

## 1. Controller/operator details
Before external use, insert and verify:
- Legal entity: [TO BE ADDED]
- Registration number: [TO BE ADDED]
- Postal address: [TO BE ADDED]
- Privacy/support email: [TO BE ADDED]

## 2. What Vexmera does
Vexmera is an AI-powered marketing platform that helps businesses connect marketing/analytics data, understand performance and receive recommended next actions.

During Private Beta, supported Google Ads and Meta Ads integrations are intended to be read-only. External campaign execution, Autopilot execution and Meta execution scope are disabled in production. Vexmera must not autonomously publish ads, change budgets, bids, targeting or campaign state during this beta posture.

## 3. Personal data and business data Vexmera may process
Depending on enabled features, Vexmera may process:

### Account and workspace data
- email address, password hash and authentication/session data;
- workspace name, company profile, onboarding profile, roles and team membership;
- invitations, preferences and product settings;
- subscription plan and billing status.

### Connected marketing and analytics data
- Google Analytics traffic/conversion metrics;
- Google Ads account/campaign metadata and reporting metrics such as impressions, clicks, conversions, value and spend;
- Meta Ads account/campaign reporting data;
- provider account identifiers and encrypted OAuth credentials needed to perform authorized reads.

OAuth secrets, API keys and provider tokens are not intended to appear in normal user-facing diagnostics.

### AI and product data
- instructions/questions submitted to Vexmera;
- selected business/workspace context supplied to AI-powered features;
- generated analyses and recommendations;
- product usage events, approvals, runs, notifications and technical diagnostics.

### Billing data
Stripe handles payment details used in Checkout. Vexmera stores billing state such as Stripe customer/subscription identifiers, plan, status, trial date and idempotent billing-event records. Vexmera does not store full payment-card numbers.

### Transactional email
Vexmera may process recipient email addresses, message content and delivery context needed to send account/service email through the configured email provider.

## 4. Why data is processed
Purposes may include:
- providing and securing the service;
- authenticating users and managing workspaces;
- retrieving authorized reporting data;
- calculating KPIs and recommendations;
- providing AI-assisted analysis;
- diagnosing reliability/security issues;
- processing subscriptions and transactional email;
- measuring optional analytics where consent is required and provided;
- complying with applicable legal obligations.

## 5. Legal bases
For EEA/UK users, applicable bases may include contract performance, legitimate interests, consent where required and legal obligation. Final publication must map each material activity to the exact legal basis after legal review.

## 6. Google and Meta connections
Connection occurs through provider authorization flows. Vexmera stores resulting credentials in encrypted form.

Authorized workspace owners/admins can disconnect supported Google/Meta connections. The current implementation removes the locally stored connector credential and saved provider/account identifiers, stops future synchronization through that credential and performs best-effort upstream revocation where supported.

Disconnecting does **not** automatically delete previously synchronized reporting history. A separate destructive synchronized-history deletion control exists so access credentials and historical reporting are not accidentally removed together.

## 7. Synchronized-history deletion
An authorized owner/admin can separately delete supported synchronized reporting history after explicit confirmation. The current implementation removes synchronized campaign-performance rows, imported provider KPI rows, anomalies and anomaly notifications. Manually entered KPI rows remain.

This operation does not delete the Vexmera account, company profile, connector credential, AI history or billing records.

## 8. Self-service account deletion
Vexmera implements a guarded account-deletion flow with a deletion preview, current-password re-authentication and exact destructive confirmation.

Deletion is blocked when an owned workspace still has another member or an active attached subscription. When allowed, eligible solo-owned local workspaces and their cascaded application data are deleted, memberships in workspaces owned by others are removed, pending invitations/queued application email for the user are removed, and the active session is cleared. Google/Meta revocation is attempted before local deletion for solo-owned workspaces.

Third-party billing, accounting, security, anti-fraud or compliance records are not represented as guaranteed deleted where Vexmera or a processor may be required or permitted to retain them.

## 9. Optional Vexmera analytics
Authenticated Vexmera pages can offer optional Google Analytics. The current implementation defaults analytics and ad-related Google consent storage to denied and does not load the analytics script until the user explicitly allows statistics. Google Signals and ad-personalization signals are disabled. Cookie settings can be reopened and consent changed later. Withdrawal triggers denied consent and best-effort deletion of first-party `_ga` cookies visible to the application origin.

## 10. Retention
### Implemented short-lived capability retention
- Sessions: 14-day expiry; expired rows are pruned and active sessions are capped at 20 per user.
- Password-reset links: 60-minute expiry; a new reset request supersedes older reset capabilities for that account.
- Workspace invitations: 7-day expiry; re-inviting the same email to the same workspace supersedes older outstanding invitations.
- Connector credentials: removed locally when supported disconnect completes.
- Synchronized reporting history: removable through the dedicated owner/admin deletion control.
- Eligible local account/workspace data: removed through self-service account deletion as described above.
- Current Neon point-in-time recovery/history setting: 6 hours. This is infrastructure recovery configuration, not a universal processor-retention promise.

### Proposed longer-lived product-data retention
Engineering has prepared `RETENTION_POLICY_PROPOSAL.md` with proposed periods for active workspace data, synchronized marketing history, AI history, competitor snapshots, usage/security logs, beta feedback, transactional email metadata and billing records.

Those proposed periods are **not yet public commitments**. Before publication, engineering must verify/implement scheduled deletion for every category given a concrete period, and owner/legal review must confirm any statutory accounting/tax requirements.

## 11. Service providers and subprocessors
The production stack currently includes Vercel (hosting/runtime), Neon (database), OpenAI API (AI processing), Stripe (billing) and Resend (transactional email). Google and Meta are connected external platforms for authorized reporting/OAuth flows.

A technical inventory is maintained in `SUBPROCESSOR_DATA_INVENTORY.md`. Vercel, OpenAI, Stripe and Resend publish current data-processing/subprocessor materials; Neon account-specific DPA/region/subprocessor details still require final account-level verification before public legal wording is finalized.

Provider roles are activity-specific. Some providers may act as processors for customer data while also acting as independent controllers for certain account, payment, service-generated or compliance data.

## 12. AI processing
The current production stack uses OpenAI API services for AI-powered analysis. Relevant user instructions, selected business context and selected marketing data may be sent to the API to generate analyses/recommendations.

Before external launch, the exact Vexmera API account/project data controls, applicable DPA, retention settings and transfer safeguards must be confirmed against the production account.

## 13. Security
Vexmera uses HTTPS, secure session settings, encrypted connector credential storage, access controls, execution locks, CSRF protections, security headers and safeguards intended to prevent secrets from appearing in user-visible diagnostics. No system can guarantee absolute security.

## 14. International transfers
Some providers may process data outside Sweden/EEA. Where required, applicable adequacy decisions, Standard Contractual Clauses or other lawful transfer mechanisms must be verified provider by provider before final publication.

## 15. User rights
Depending on applicable law, individuals may have rights to access, correction, deletion, restriction, objection, portability, withdrawal of consent and complaint to a data-protection authority.

A verified privacy contact channel must be inserted before external use. Product disconnect/history/account deletion controls support data control but do not replace a broader rights-request process.

## 16. Business-customer data
Where a business customer connects or supplies personal data relating to its own customers, employees or other individuals, the business may be controller and Vexmera may be processor for some activities. A Data Processing Agreement may therefore be required. Roles must be mapped per activity rather than assumed globally.

## 17. Children's data
Vexmera is intended for business users and is not designed for children. Any final age requirement must be legally reviewed and reflected in production terms.

## 18. Changes and contact
Material policy changes should be communicated appropriately and the effective date updated.

Privacy/support contact: [TO BE ADDED BEFORE EXTERNAL USE]

## Internal review references
- `RETENTION_POLICY_PROPOSAL.md`
- `SUBPROCESSOR_DATA_INVENTORY.md`
- `DATA_HANDLING.md`
- `LEGAL_REVIEW_PREP.md`
- `PRODUCTION_ENVIRONMENT.md`
- `DEPLOY_CHECKLIST.md`

Where documentation conflicts, verified implementation and qualified legal review control.