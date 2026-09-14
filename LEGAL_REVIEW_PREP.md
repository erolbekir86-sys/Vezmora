# Vexmera — legal review preparation

> Private-beta preparation document. This is an engineering/product inventory for legal review, not legal advice and not a published Privacy Policy or Terms of Service.

Last reviewed: 2026-09-14

## Purpose

Before Vexmera invites external pilot companies or enables live paid billing, legal review should be able to answer four practical questions without reverse-engineering the product:

1. Who is the contracting/legal entity and how can customers contact it?
2. What personal, account and marketing data does Vexmera process, for what purpose, and for how long?
3. Which external providers receive data, in what role, and under which contractual/transfer safeguards?
4. What can a customer delete, disconnect, export or control directly in the product?

The codebase already implements substantial technical controls. This file tracks the remaining policy and contractual decisions.

## 1. Legal entity and public contact details — owner/legal input required

Do not publish placeholders or inferred personal details as facts. Confirm:

- [ ] Full legal business name
- [ ] Swedish organisation/registration number, if applicable
- [ ] Registered/postal address where required
- [ ] Privacy/contact email
- [ ] Support/contact email
- [ ] VAT registration details, if applicable
- [ ] Governing-law / dispute wording for customer terms
- [ ] Whether the five-company pilot is contracted with businesses only

### Current contact inconsistency

The public marketing footer and the published Privacy/Terms pages do not currently use one verified contact address. Domain mail forwarding for `vexmera.com` has been observed as active, but that does **not** prove that a particular alias such as `hello@...`, `support@...` or `privacy@...` exists or is monitored.

Do not change DNS/domain configuration or publish a new domain alias until the owner has explicitly selected and verified the address.

## 2. Product posture to describe accurately

Current private-beta posture:

- Vexmera is an AI-driven marketing intelligence and decision-support service.
- Google and Meta connector paths are read-oriented in private beta.
- External advertising mutations are disabled by server-side execution locks.
- Recommendations and approval items can be prepared without enabling autonomous external execution.
- Google Ads **Explorer Access** was approved for the Cloud project owning the deployed OAuth client on 2026-09-12.
- A real Google Ads production read-only sync has succeeded with campaign-level rows, so Basic Access is not a blocker for the current five-company read-only pilot.
- Basic Access remains a future quota/functionality upgrade if Explorer limits become insufficient. Google's current upgrade flow requires OAuth Brand Verification; the legacy pre-2026-09-09 pending application is not an active review path.
- Meta read-only access has been verified against a connected account, including a legitimate zero-row empty-data result.
- Stripe billing remains test-mode launch verification. The current test catalog and webhook exist, but fresh Checkout/trial/webhook/Customer Portal E2E has not yet passed and no test Billing Portal configuration was present during the latest check.

Public legal text must avoid promises broader than the actual implementation.

## 3. Data categories currently processed

Legal review should map each category to purpose, lawful basis/contractual necessity, retention, access, deletion and recipients.

### Account and authentication

Examples:

- email address
- password-derived authentication material
- session data
- workspace membership and role
- invitations

Verified technical retention/safety:

- authenticated sessions expire after 14 days;
- active sessions are bounded to the newest 20 per user after expired-session pruning;
- password-reset links expire after 60 minutes and a new reset supersedes older outstanding reset capabilities;
- workspace invitations expire after 7 days and a new pending invite supersedes an older pending invite for the same workspace/address;
- password reset revokes existing authenticated sessions.

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

Active account/workspace retention still requires a final public rule, subject to the implemented account-deletion controls and legal exceptions.

### Connected marketing account data

Examples:

- Google/Meta connection status
- account/property identifiers
- encrypted OAuth credential material
- granted scopes and sync metadata

Current controls:

- Google/Meta can be disconnected in-product by authorized owner/admin roles;
- local connector credentials are removed even if upstream revocation cannot be completed;
- provider-side revocation is best-effort;
- credentials/tokens are excluded from normal customer responses and secret-safe diagnostics.

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
- manually entered KPI rows are intentionally preserved by the synchronized-history deletion control;
- Google Analytics sessions are treated as website sessions rather than paid-ad clicks at the read boundary.

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

Vexmera account deletion must not promise that Stripe or another processor will erase records that the processor or merchant must retain for accounting, disputes, fraud prevention, security or legal duties.

## 4. External provider review matrix

The services below reflect the current engineering/operations stack. Legal review must verify actual account configuration, contract/DPA role, data location, retention and transfer position before publishing a final subprocessor list.

| Provider | Current technical purpose | Data that may be involved | Review status |
| --- | --- | --- | --- |
| Vercel | Hosting/serverless deployment | HTTP requests, runtime and technical logs | Verify DPA/role, regions, retention and transfer safeguards |
| Neon | PostgreSQL database | Account/workspace/product data | Verify DPA/role, selected region, backup/PITR and deletion behavior |
| OpenAI | AI inference | Prompts, business/workspace context and generated output | Verify configured account's applicable data terms, retention, DPA and transfer position before public wording |
| Stripe | Test billing now; future subscription/payment operations | Customer/billing identifiers and payment/subscription records | Verify merchant/controller/processor allocation, DPA, statutory retention and live tax obligations |
| Resend / configured SMTP provider | Transactional email | Recipient, message content and delivery metadata | Verify actual account/provider, DPA, log retention and transfers |
| Google | OAuth, GA4 reporting, Google Ads reporting, optional analytics after consent | OAuth/account identifiers, marketing reports, optional analytics data | Separate connected-customer data from website analytics; verify contractual roles and transfer terms |
| Meta | OAuth and Ads read-only reporting | OAuth/account identifiers and advertising performance data | Verify platform terms, DPA/data-transfer position and read-only beta scope |
| ImprovMX, if used for customer/privacy aliases | Domain email forwarding | Incoming support/privacy email and forwarding metadata | Verify whether a public alias is actually used, monitored and should be included in disclosures |

Do not copy this matrix directly into public legal text until account-specific details are verified.

## 5. Website analytics and cookies

Current authenticated-app implementation:

- optional Google Analytics storage defaults to denied;
- Google Analytics is not embedded in initial authenticated HTML;
- analytics loads only after explicit opt-in;
- ad storage, ad user data and ad personalization remain denied;
- Google Signals/ad-personalization signals remain disabled;
- Cookie settings can be reopened later;
- first-party `_ga` cookies are best-effort cleared when analytics is denied or withdrawn.

Legal/content work still required:

- [ ] Final Swedish and English cookie notice wording
- [ ] Confirm analytics policy for the public marketing landing page
- [ ] Cookie table with provider, purpose and actual lifetime based on final deployment
- [ ] Confirm consent-record approach for the intended legal position

Do not describe analytics as anonymous unless legal/technical review supports that wording.

## 6. Deletion and customer controls technically supported

### Disconnect Google/Meta

Removes locally stored connector credentials, clears saved account identifiers/configuration, stops future synchronization and attempts provider-side revocation. Previously synchronized reporting history remains until separately deleted.

### Delete synchronized marketing history

Deletes provider-synchronized campaign metrics, provider KPI rows and related anomaly data after separate destructive confirmation. Manually entered KPI rows remain.

### Delete Vexmera account

After blocker preview, current-password re-authentication and exact final confirmation, the local Vexmera account can be deleted. Solo-owned workspaces are deleted when safe; memberships in another owner's workspace are removed without deleting that shared workspace. Google/Meta token revocation is attempted before local deletion.

Public documentation must keep these three operations distinct.

## 7. Retention decisions required before external pilot onboarding

Concrete short-lived capability periods already match implementation:

| Category | Verified technical rule |
| --- | --- |
| Authenticated sessions | 14-day expiry; newest 20 active sessions per user retained after pruning |
| Password-reset capability | 60-minute expiry; new request supersedes older outstanding reset capability |
| Workspace invitation | 7-day expiry; newer pending invite supersedes older pending invite for same workspace/address |
| OAuth connector credential | Retained while connection is active; local copy removed on supported disconnect/account deletion |

Observed infrastructure evidence:

- the current Neon project has a 6-hour history-retention/PITR setting at the time of the latest engineering check.

That Neon setting must not be generalized into a public backup-retention promise until provider/account behavior and legal wording are reviewed.

Still requiring a production rule:

| Category | Decision needed |
| --- | --- |
| Active account/workspace data | Retain while relationship is active, subject to deletion controls and legal exceptions |
| AI run history / generated outputs | Choose a defined operational/customer-controlled retention period |
| Synced campaign/KPI history | Customer-controlled while active; explicit history deletion exists |
| Competitor snapshots | Choose a defined rolling retention period and add cleanup if needed |
| Beta feedback | Choose pilot/research retention or anonymization rule |
| Email delivery/outbox records | Define local/provider operational retention |
| Security/application logs | Choose minimum period required for security/debugging and verify provider settings |
| Database backups/recovery | Verify provider/account behavior against the intended public rule |
| Stripe billing records | Set accounting/legal retention with qualified legal/accounting input; do not promise immediate erasure |

## 8. Data-subject / customer-rights workflow

Self-service deletion exists, but the operating procedure still needs an owner and response process for requests that cannot be completed entirely in-product.

- [ ] Verified contact channel for privacy requests
- [ ] Proportionate identity-verification procedure
- [ ] Access request workflow
- [ ] Rectification workflow
- [ ] Export/portability workflow and supported format
- [ ] Restriction/objection handling where applicable
- [ ] Processor/platform escalation path
- [ ] Response logging without unnecessary request-content retention

## 9. Beta Terms topics for legal review

Pilot terms should address:

- private-beta / pre-release status;
- business-use scope and authorized users;
- customer responsibility for lawful connection of advertising/analytics accounts;
- read-only advertising execution posture in the current beta;
- AI output limitations and customer responsibility for final decisions;
- confidentiality and feedback;
- availability/support expectations without unsupported SLA promises;
- subscription/trial wording only if billing is actually enabled for the pilot;
- termination, deletion and retained billing/legal records;
- acceptable use;
- limitation of liability and governing-law wording drafted/reviewed appropriately.

## 10. Gate before first external pilot company

Do not mark legal readiness complete until all applicable items are true:

- [ ] Legal entity/contact details supplied and verified
- [ ] Privacy Policy reviewed and published consistently
- [ ] Beta Terms reviewed and published/accepted
- [ ] Cookie wording/settings reviewed
- [ ] Processor/subprocessor matrix verified against actual accounts/contracts
- [ ] International-transfer safeguards reviewed where applicable
- [ ] Longer-lived retention periods selected and matched to infrastructure behavior
- [ ] Data-rights operating procedure assigned
- [ ] VAT/tax treatment decided before live paid launch
- [x] Canonical production domain is `vexmera.com` and legal pages are reachable over HTTPS

## Engineering references

Use these internal documents together during review:

- `DATA_HANDLING.md`
- `PRODUCTION_ENVIRONMENT.md`
- `DEPLOY_CHECKLIST.md`
- `STRIPE_SANDBOX_CATALOG.md`
- `META_OAUTH_SETUP.md`
- `GOOGLE_ADS_STATUS.md`

When implementation, provider terms or legal analysis is uncertain, keep a TODO rather than converting an assumption into a public promise.
