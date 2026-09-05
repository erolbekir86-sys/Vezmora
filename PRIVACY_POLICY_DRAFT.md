# Vexmera Privacy Policy — DRAFT

> **Status:** Draft for private-beta preparation. This is not final legal text and must be reviewed and completed with the operator's legal entity, address, contact details, retention periods, subprocessors and any other jurisdiction-specific requirements before external launch.

**Last updated:** 2026-09-05

## 1. Who this policy applies to
This policy describes how Vexmera handles personal data when a user creates an account, connects marketing or analytics services, uses AI-powered marketing analysis, or participates in a private beta.

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
- Name and email address
- Authentication and session data
- Workspace name, business profile and preferences
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
- Generated recommendations and analyses
- Product usage events, error diagnostics and technical logs
- Approval or workflow status where applicable

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
- Comply with applicable legal obligations

## 5. Legal bases
For users in the EEA/UK, the applicable legal basis depends on the processing activity and may include:
- Performance of a contract
- Legitimate interests, such as securing and improving the service
- Consent, where required
- Compliance with legal obligations

The final production policy should map each material processing purpose to its precise legal basis.

## 6. Google and Meta connections
When a user connects Google or Meta, authentication occurs through the provider's authorization flow. Vexmera stores the resulting authorization credentials in encrypted form so that it can access the data the user has permitted.

Vexmera now includes a product-level disconnect control for supported Google and Meta connections. Disconnecting is restricted to authorized workspace owners or administrators. When a supported account is disconnected, Vexmera removes its locally stored connector credential and saved connector/account identifiers, stops future sync access through that credential, and performs a best-effort provider-side revocation where supported.

Provider-side revocation may also be performed directly through the relevant Google or Meta account controls. A provider or network failure during revocation does not prevent Vexmera from deleting its own stored credential copy.

**Disconnecting an account does not currently delete previously synchronized campaign or KPI history.** Retained reporting history must be deleted through a separate explicit deletion process once that production control is implemented. Until then, Vexmera must not describe the disconnect action as a complete purge of all historical marketing data.

Vexmera must not expose OAuth tokens, developer tokens, API keys or provider secrets in user-visible diagnostics.

## 7. AI providers
Vexmera may send relevant user instructions, business context and selected marketing data to an AI service provider in order to generate analyses and recommendations.

Before external launch, the final policy must identify the relevant AI provider(s), the categories of data sent, retention settings where applicable, international-transfer safeguards and the contractual role of each provider.

## 8. Service providers and subprocessors
Vexmera may use service providers for functions such as hosting, databases, AI processing, payments, email delivery, monitoring and authentication.

A production subprocessor list should be published before external launch. Current technical infrastructure may include providers used for hosting, database services, payments, email delivery and AI processing.

## 9. Data retention
Vexmera should keep personal data only for as long as needed for the purposes described in this policy, including providing the service, resolving disputes, enforcing agreements and meeting legal obligations.

Before external launch, define concrete retention rules for:
- Account and workspace data
- Connected campaign and analytics data
- OAuth credentials
- Technical logs
- AI request/response records
- Deleted accounts and backups

Connector credentials are removed from Vexmera's active connector record when the supported self-service disconnect action completes. This does not by itself determine the retention period for previously synchronized reporting data.

## 10. Security
Vexmera uses technical and organizational safeguards intended to protect data, including encrypted credential storage, HTTPS, secure session settings, access controls and safeguards designed to prevent secrets from appearing in user-visible diagnostics.

No system can guarantee absolute security.

## 11. International data transfers
Some service providers may process data outside the user's country or the EEA. Where required, Vexmera should rely on legally recognized transfer safeguards such as adequacy decisions or Standard Contractual Clauses.

The final policy must identify the applicable transfer mechanisms.

## 12. User rights
Depending on location, users may have rights to:
- Access personal data
- Correct inaccurate personal data
- Request deletion
- Restrict or object to certain processing
- Request data portability
- Withdraw consent where processing relies on consent
- Complain to a data-protection authority

The final policy should provide a verified privacy contact channel for exercising these rights. A dedicated production process for complete historical-data deletion and account-deletion requests must be finalized before external launch.

## 13. Business-customer data
Where a business customer provides or connects data relating to its own customers, employees or other individuals, the business may act as controller and Vexmera may act as processor for some processing activities.

A Data Processing Agreement may therefore be required before external customer use.

## 14. Children's data
Vexmera is intended for business users and is not designed for children. The production service should define and enforce any minimum-age requirement that applies.

## 15. Changes to this policy
Vexmera may update this policy as the service changes. Material changes should be communicated appropriately and the effective date should be updated.

## 16. Contact
Privacy contact: [TO BE ADDED BEFORE EXTERNAL USE]
