# Vexmera — legal review preparation

> Private-beta preparation document. This is an engineering/product inventory for legal review, not legal advice and not a published Privacy Policy or Terms of Service.

## Purpose

Before Vexmera invites external pilot companies or enables live paid billing, legal review should be able to answer four practical questions without reverse-engineering the product:

1. Who is the contracting/legal entity and how can customers contact it?
2. What personal, account and marketing data does Vexmera process, for what purpose, and for how long?
3. Which external providers receive data, in what role, and under which contractual/transfer safeguards?
4. What can a customer delete, disconnect, export or control directly in the product?

The codebase already implements substantial technical controls. This file tracks the remaining policy and contractual decisions.

## 1. Legal entity and public contact details — must be supplied

Do not publish placeholders as facts. Legal review must confirm:

- [ ] Full legal business name
- [ ] Swedish organisation number, if applicable
- [ ] Registered/postal address
- [ ] Privacy/contact email
- [ ] Support/contact email
- [ ] VAT registration details, if applicable
- [ ] Governing-law / dispute wording for customer terms
- [ ] Whether the five-company pilot is contracted with businesses only

## 2. Product posture to describe accurately

Current private-beta posture:

- Vexmera is an AI-driven marketing intelligence and decision-support service.
- Google and Meta connector paths are read-oriented in private beta.
- External advertising mutations are disabled by server-side execution locks.
- Recommendations and approval items can be prepared without enabling autonomous external execution.
- Google Ads API Basic Access and manager-account linking are separate external prerequisites and must not be described as completed until actually verified.
- Stripe billing is still in test mode for launch verification and must not be presented as live paid production until the sandbox and tax/legal work are complete.

Public legal text should avoid promises broader than the actual implementation.

## 3. Data categories currently processed

Legal review should map each category to purpose, lawful basis/contractual necessity, retention, access, deletion and recipients.

### Account and authentication

Examples:

- email address
- password-derived authentication material
- session data
- workspace membership and role
- invitations

Current controls:

- self-service account deletion exists;
- current-password re-authentication and exact destructive confirmation are required;
- deletion is blocked while an owned workspace has other members or an active attached subscription.

### Company/workspace profile

Examples:

- company name
- industry
- market
- website
- target audience
- offer description
- brand voice
- goals and workspace settings

### Connected marketing account data

Examples:

- Google/Meta connection status
- account/property identifiers
- encrypted OAuth credential material
- granted scopes and sync metadata

Current controls:

- Google/Meta can be disconnected in-product;
- local connector credentials are removed even if upstream revocation cannot be completed;
- provider-side revocation is best-effort.

### Marketing performance data

Examples:

- campaign identifiers/names
- dates
- impressions
- clicks
- conversions
- spend
- attributed revenue/value
- currency
- derived KPI rows
- anomaly/signal records

Current controls:

- synchronized marketing history can be deleted separately from connector credentials;
- manual KPI rows are intentionally preserved by the synchronized-history deletion control.

### AI inputs and outputs

Potential categories:

- user prompts/instructions
- company context supplied to Core/Pulse/Launch
- generated analyses, strategies and campaign proposals
- AI run metadata/history

Decision still required:

- [ ] Exact production retention period for AI run history and generated outputs
- [ ] Whether customers need a separate delete/export control for AI history before general availability

### Competitor monitoring

Potential categories:

- competitor names/URLs
- customer-supplied monitoring notes
- public-page snapshots or detected changes

Decision still required:

- [ ] Retention period for competitor records/snapshots
- [ ] Public wording clarifying that only public web material is intended to be monitored

### Billing and transactional email

Potential categories:

- Stripe customer/subscription identifiers and billing state
- transactional email recipient and delivery queue records

Important distinction:

- Vexmera account deletion must not promise that Stripe or another processor will erase records that the processor or merchant must retain for accounting, disputes, fraud prevention, security or legal duties.

## 4. External provider review matrix

The names below reflect services currently used or configured in the Vexmera stack. Legal review must verify the actual contract/account configuration, data locations, DPA terms and international-transfer position before publishing a final subprocessor list.

| Provider | Current technical purpose | Data that may be involved | Role / legal review question | Status |
| --- | --- | --- | --- | --- |
| Vercel | Hosting/serverless deployment | HTTP requests, application runtime data, technical logs | Confirm processor/subprocessor role, DPA, regions and transfer safeguards | TODO |
| Neon | PostgreSQL database | Account/workspace/product data stored by Vexmera | Confirm processor role, selected region, DPA, backups and deletion behavior | TODO |
| OpenAI | AI inference for Core/Pulse/Launch | Prompts, workspace/business context and generated output | Confirm API data terms, retention settings, DPA and transfer position for the configured account | TODO |
| Stripe | Test billing now; future subscriptions/payment operations | Customer/billing identifiers and payment/subscription records | Confirm controller/processor allocation, merchant obligations, DPA and statutory retention | TODO |
| Resend / configured SMTP provider | Transactional email | Email address, message content and delivery metadata | Confirm actual provider/account, DPA, log retention and transfer safeguards | TODO |
| Google | OAuth, GA4 reporting, Google Ads reporting, optional website analytics after consent | OAuth/account identifiers, marketing reports; analytics device/browser data after opt-in | Separate API-connected customer data from website analytics; verify Google contractual roles and transfer terms | TODO |
| Meta | OAuth and Ads read-only reporting | OAuth/account identifiers and advertising performance data | Verify platform terms, DPA/data-transfer position and private-beta read-only scope | TODO |

Do not copy this matrix directly into public legal text until the account-specific details have been verified.

## 5. Website analytics and cookies

Current authenticated-app implementation:

- optional Google Analytics storage defaults to **denied**;
- Google Analytics is not embedded in initial authenticated HTML;
- analytics loads only after explicit opt-in;
- ad storage, ad user data and ad personalization remain denied;
- Google Signals is disabled;
- ad-personalization signals are disabled;
- Cookieinställningar can be reopened later;
- first-party `_ga` cookies are best-effort cleared when analytics is denied or consent is withdrawn.

Legal/content work still required:

- [ ] Final Swedish and English cookie notice wording
- [ ] Confirm whether analytics is also intended on the public marketing landing page
- [ ] Cookie table with provider, purpose and actual lifetime based on final configuration
- [ ] Confirm consent-record approach is sufficient for the selected deployment and legal position

The consent banner must not describe analytics as “anonymous” unless legal/technical review confirms that wording is supportable.

## 6. Deletion and user-control claims that are technically supported

Vexmera currently supports these distinct operations:

### Disconnect Google/Meta

Removes locally stored connector credentials, clears saved account identifiers/configuration, stops future synchronization and attempts provider-side token revocation. Previously synchronized reporting history remains until separately deleted.

### Delete synchronized marketing history

Deletes provider-synchronized campaign metrics, provider KPI rows and related anomaly data after separate destructive confirmation. Manually entered KPI rows remain.

### Delete Vexmera account

After blocker preview, current-password re-authentication and exact final confirmation, the local Vexmera account can be deleted. Solo-owned workspaces are deleted when safe; memberships in other owners' workspaces are removed without deleting those shared workspaces. Google/Meta token revocation is attempted before local deletion.

Public documentation must keep these three operations distinct.

## 7. Retention decisions required before external pilot onboarding

No concrete duration should be published until engineering and legal agree that the infrastructure actually follows it.

For each category below, select a production rule and verify implementation:

| Category | Proposed decision to review | Engineering verification needed |
| --- | --- | --- |
| Active account/workspace data | Retain while account/service relationship is active, subject to customer deletion controls | Confirm database deletion/cascade behavior and exceptions |
| AI run history / generated outputs | Choose a short operational retention period or customer-controlled retention | Confirm actual tables/jobs and cleanup mechanism |
| Synced campaign/KPI history | Customer-controlled while account is active; explicit delete-history control already exists | Confirm no hidden duplicate stores |
| Competitor snapshots | Choose a defined rolling retention period | Add cleanup job if a limit is adopted |
| Beta feedback | Choose a defined pilot/research retention period | Add cleanup or anonymization process if required |
| Email delivery/outbox records | Keep only as long as operationally necessary | Confirm provider + local outbox retention |
| Security/application logs | Choose minimum period needed for security/debugging | Verify Vercel/provider log settings |
| Database backups/recovery | Match documented backup window to Neon configuration | Verify actual backup/PITR configuration |
| Stripe billing records | Retain according to merchant/accounting/legal obligations and Stripe capabilities | Legal/accounting decision; do not promise immediate erasure |

## 8. Data subject / customer rights workflow

Self-service deletion exists, but the operating procedure still needs an owner and response process for requests that cannot be completed entirely in-product.

- [ ] Contact channel for privacy requests
- [ ] Identity-verification procedure proportional to the request
- [ ] Access request workflow
- [ ] Rectification workflow
- [ ] Export/portability workflow and supported format
- [ ] Restriction/objection handling where applicable
- [ ] Processor/platform escalation path where data cannot be removed directly by Vexmera
- [ ] Response logging without retaining unnecessary request content

## 9. Beta Terms topics for legal review

The pilot terms should explicitly address:

- private-beta / pre-release status;
- business-use scope and authorized users;
- customer responsibility for lawful connection of advertising/analytics accounts;
- read-only advertising execution posture in the current beta;
- AI output limitations and customer responsibility for final marketing decisions;
- confidentiality and feedback;
- availability/support expectations without unsupported SLA promises;
- subscription/trial language only if billing is actually enabled for the pilot;
- termination, account deletion and retained billing/legal records;
- acceptable use;
- limitation of liability and governing-law language drafted by qualified counsel.

## 10. Gate before first external pilot company

Do not mark legal readiness complete until all of the following are true:

- [ ] Legal entity/contact details supplied
- [ ] Privacy Policy reviewed and published
- [ ] Beta Terms reviewed and published/accepted
- [ ] Cookie wording and settings reviewed
- [ ] Processor/subprocessor matrix verified against actual accounts/contracts
- [ ] International-transfer safeguards reviewed where applicable
- [ ] Retention periods selected and matched to infrastructure behavior
- [ ] Data-rights operating procedure assigned
- [ ] VAT/tax treatment decided before any live paid launch
- [ ] Canonical production domain chosen and legal links point to real pages

## Engineering references

Use these internal documents together during review:

- `DATA_HANDLING.md`
- `PRODUCTION_ENVIRONMENT.md`
- `DEPLOY_CHECKLIST.md`
- `STRIPE_SANDBOX_CATALOG.md`
- `META_OAUTH_SETUP.md`

This preparation file should remain conservative: when implementation, provider terms or legal analysis is uncertain, record a TODO rather than converting an assumption into a public promise.
