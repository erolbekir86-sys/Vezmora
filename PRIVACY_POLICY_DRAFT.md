# Vexmera Privacy Policy — DRAFT

> **Status:** Draft for private-beta preparation. This is not final legal text and must be reviewed and completed with the operator's legal entity, address, contact details, retention periods, verified processor/subprocessor information and any other jurisdiction-specific requirements before external launch.

**Last updated:** 2026-09-05

## 1. Who this policy applies to
This policy describes how Vexmera handles personal data when a user creates an account, connects marketing or analytics services, uses AI-powered marketing analysis, visits authenticated product pages where optional analytics may be offered, or participates in a private beta.

Before external use, insert the legal controller/operator details here:
- Legal entity: [TO BE ADDED]
- Registration number: [TO BE ADDED]
- Postal address: [TO BE ADDED]
- Privacy contact email: [TO BE ADDED]

## 2. What Vexmera is
Vexmera is an AI-powered marketing platform intended to help businesses understand marketing performance, identify opportunities and receive recommendations about what to do next.

During the private beta, connected advertising and analytics integrations are intended to operate in **read-only mode**. Vexmera must not autonomously publish ads, change budgets, bids or campaign settings unless a later production version explicitly enables those features with appropriate permissions and user controls.

## 3. Data Vexmera may process
Depending on which features a user enables, Vexmera may process:

### Account and workspace data
- Email address and account authentication data
- Session data
- Workspace name, business profile, role and preferences
- Invitations and team membership
- Subscription and billing status

### Connected marketing and analytics data
When a user connects a supported provider, Vexmera may retrieve data that the user has authorized the provider to share, such as:
- Google Analytics traffic and conversion metrics
- Google Ads campaign names, IDs, dates, impressions, clicks, conversions, conversion value, spend and account currency
- Meta Ads account and campaign performance data
- Other marketing performance data added in future supported integrations

Vexmera does not require users to paste OAuth access tokens, developer tokens or API secrets into ordinary chat or support messages.

### AI and product usage data
- Questions or instructions submitted to Vexmera
- Relevant business/workspace context supplied to AI-powered features
- Generated recommendations and analyses
- Product usage events, error diagnostics and technical logs
- Approval or workflow status where applicable

### Optional website analytics data
The authenticated Vexmera application can offer optional Google Analytics. The current implementation defaults analytics and advertising-related Google consent storage to **denied** and does not load the Google Analytics script until the user explicitly allows statistics.

Google Signals and ad-personalization signals are disabled in the current implementation. The user can reopen Cookieinställningar and change the analytics choice later. When analytics is denied or consent is withdrawn, Vexmera updates consent to denied and performs best-effort deletion of first-party `_ga` cookies visible to the application origin.

The final production policy and cookie notice must document the actual cookies, lifetimes and provider roles used by the final deployment.

## 4. Why Vexmera processes data
Vexmera may process personal data to:
- Provide and operate the service
- Authenticate users and protect accounts
- Retrieve authorized marketing and analytics data
- Calculate reports, KPIs and recommendations
- Provide AI-assisted analysis
- Diagnose errors and improve reliability
- Process subscriptions and payments
- Send transactional service communications
- Protect the service against abuse, fraud and security threats
- Measure optional product usage where the user has provided any consent required for that analytics processing
- Comply with applicable legal obligations

## 5. Legal bases
For users in the EEA/UK, the applicable legal basis depends on the processing activity and may include:
- Performance of a contract
- Legitimate interests, such as securing and operating the service
- Consent, where required, including optional analytics where applicable
- Compliance with legal obligations

The final production policy must map each material processing purpose to its precise legal basis after legal review.

## 6. Google and Meta connections
When a user connects Google or Meta, authentication occurs through the provider's authorization flow. Vexmera stores the resulting authorization credentials in encrypted form so that it can access the data the user has permitted.

Vexmera includes a product-level disconnect control for supported Google and Meta connections. Disconnecting is restricted to authorized workspace owners or administrators. When a supported account is disconnected, Vexmera removes its locally stored connector credential and saved connector/account identifiers, stops future sync access through that credential, and performs a best-effort provider-side revocation where supported.

Provider-side revocation may also be performed directly through the relevant Google or Meta account controls. A provider or network failure during revocation does not prevent Vexmera from deleting its own stored credential copy.

**Disconnecting an account does not delete previously synchronized campaign or KPI history.** Vexmera provides a separate destructive control for synchronized reporting history so that connection access and retained reporting data are not accidentally deleted together.

Vexmera must not expose OAuth tokens, developer tokens, API keys or provider secrets in user-visible diagnostics.

## 7. Deleting synchronized marketing history
For supported private-beta workspaces, an authorized workspace owner or administrator can separately request deletion of synchronized marketing/reporting history. The current implementation requires a separate typed confirmation before the deletion request is sent.

This control removes:
- Synchronized campaign-performance rows
- KPI rows imported from Google Analytics, Google Ads or Meta Ads
- Anomaly records and anomaly notifications derived from synchronized reporting data

The control intentionally retains:
- Manually entered KPI rows
- Connector credentials and connection state
- Account and workspace records
- Company/brand profile data
- AI request and response history
- Billing/subscription records
- Other product records not listed above

Accordingly, this feature is a scoped reporting-history deletion control, not the same operation as deleting a Vexmera account.

## 8. Self-service account deletion
Vexmera also implements a separate guarded account-deletion flow.

Before irreversible deletion, the authenticated user can request a deletion preview showing whether the account can currently be deleted and what local data is in scope. The final deletion request requires the user's current password and an exact destructive confirmation phrase.

Account deletion is blocked when:
- an owned workspace still has another member; or
- an owned workspace has an attached Stripe subscription that is still treated as active.

When deletion is allowed, the current implementation:
- re-authenticates the user;
- re-checks deletion blockers immediately before local deletion;
- attempts to revoke Google and Meta OAuth credentials for solo-owned workspaces before local deletion;
- deletes the user's solo-owned workspaces and database-cascaded local workspace data;
- removes the user's membership from workspaces owned by someone else without deleting those shared business workspaces;
- deletes the local user account and authentication credentials;
- removes pending invitations and queued application email addressed to the account email;
- clears the active Vexmera session cookie.

Third-party billing, accounting, security or compliance records are **not** represented as guaranteed deleted by this local account-deletion operation. Stripe or other processors may retain records where necessary for accounting, dispute handling, fraud prevention, security or legal obligations.

The final policy must describe processor-specific retention accurately and must not promise complete third-party erasure where Vexmera cannot technically or legally guarantee it.

## 9. AI providers
Vexmera may send relevant user instructions, business context and selected marketing data to an AI service provider in order to generate analyses and recommendations.

The current production engineering stack uses OpenAI API services for AI processing. Before external launch, legal review must verify the configured account's applicable data terms, retention settings, Data Processing Agreement where required, contractual role and any international-transfer safeguards before those details are converted into final public legal wording.

## 10. Service providers and subprocessors
Vexmera may use service providers for functions such as hosting, databases, AI processing, payments, email delivery, analytics and connected advertising APIs.

The current technical stack includes or is configured to use services from Vercel, Neon, OpenAI, Stripe, an SMTP/email delivery provider, Google and Meta. This is an engineering inventory, not yet the final legally reviewed public subprocessor list.

Before external launch, Vexmera must verify the actual provider accounts, contractual roles, processing locations, applicable DPAs, transfer safeguards and processor-specific retention, then publish the appropriate disclosures.

## 11. Data retention
Vexmera should keep personal data only for as long as needed for the purposes described in this policy, including providing the service, resolving disputes, enforcing agreements and meeting legal obligations.

Before external launch, define and operationally verify concrete retention rules for:
- Active account and workspace data
- Connected campaign and analytics data
- OAuth credentials
- Technical/security logs
- AI request/response records
- Competitor monitoring records and snapshots
- Beta feedback
- Transactional email delivery records
- Database backups and recovery copies
- Processor-held billing/compliance records

Connector credentials are removed from Vexmera's active connector record when the supported self-service disconnect action completes. Synchronized reporting history can be removed separately through the scoped deletion control. The broader account-deletion flow removes the local account and eligible solo-owned workspace data as described above.

No concrete public retention period should be stated until engineering and legal review confirm that the infrastructure actually follows it.

## 12. Security
Vexmera uses technical and organizational safeguards intended to protect data, including encrypted credential storage, HTTPS, secure session settings, access controls, human-approval controls for sensitive product actions and safeguards designed to prevent secrets from appearing in user-visible diagnostics.

No system can guarantee absolute security.

## 13. International data transfers
Some service providers may process data outside the user's country or the EEA. Where required, Vexmera should rely on legally recognized transfer safeguards such as adequacy decisions or Standard Contractual Clauses.

The final policy must identify the actual applicable transfer mechanisms after provider/account-specific review.

## 14. User rights
Depending on location, users may have rights to:
- Access personal data
- Correct inaccurate personal data
- Request deletion
- Restrict or object to certain processing
- Request data portability
- Withdraw consent where processing relies on consent
- Complain to a data-protection authority

The final policy must provide a verified privacy contact channel for exercising these rights. Product-level disconnect, synchronized-history deletion and account deletion help users control data, but they do not replace an operating process for broader access, portability, objection or processor-escalation requests.

## 15. Business-customer data
Where a business customer provides or connects data relating to its own customers, employees or other individuals, the business may act as controller and Vexmera may act as processor for some processing activities.

A Data Processing Agreement may therefore be required before external customer use. The parties' roles must be reviewed for each material processing activity rather than assumed globally.

## 16. Children's data
Vexmera is intended for business users and is not designed for children. The production service should define and enforce any minimum-age requirement that applies.

## 17. Changes to this policy
Vexmera may update this policy as the service changes. Material changes should be communicated appropriately and the effective date should be updated.

## 18. Contact
Privacy contact: [TO BE ADDED BEFORE EXTERNAL USE]

## Internal review references
Before this draft is approved for publication, review it against:
- `DATA_HANDLING.md`
- `LEGAL_REVIEW_PREP.md`
- `PRODUCTION_ENVIRONMENT.md`
- `DEPLOY_CHECKLIST.md`

Any conflict should be resolved in favor of the verified implementation and qualified legal review, not marketing convenience.
