# Vexmera processor and data-handling inventory

Last reviewed: 2026-09-15

Status: technical/factual inventory for legal review. This is not itself the final public subprocessor list.

## Core production providers

### Vercel
Purpose: application hosting, serverless runtime, edge delivery and operational logs.
Likely data: request metadata, application responses, runtime logs and limited user/workspace data transiently handled by the application.
Role: generally a processor for customer data handled to provide hosting, while some service-generated/account data may be processed by Vercel as controller under its terms.
Current legal evidence: Vercel publishes a DPA and a maintained subprocessor list. The currently published DPA states that subprocessors are used under written data-protection obligations and that Vercel maintains a subprocessor list.
Launch action: verify that the Vexmera plan/account is covered by the applicable DPA before external pilot onboarding.

### Neon
Purpose: managed PostgreSQL database and point-in-time recovery.
Likely data: accounts, workspaces, company profiles, onboarding, connector state/credentials in encrypted form, synchronized campaign/KPI data, AI/product records, billing projection and application events.
Current project fact: recovery/history retention is configured to 6 hours.
Launch action: verify current Neon DPA, region/processing location, subprocessor list and contractual coverage for the production account.

### OpenAI API
Purpose: AI analysis and recommendations.
Likely data: user instructions, selected company/workspace context, relevant marketing metrics and generated AI outputs.
Current legal evidence: OpenAI publishes an API/business DPA and a current subprocessor list. For EEA/Swiss customers the current DPA identifies OpenAI Ireland Ltd. as the contracting data-processing entity where applicable.
Launch action: verify the exact Vexmera API account/project data controls, retention configuration and contractual/DPA status before final public wording.

### Stripe
Purpose: test-mode and future production subscription billing, Checkout, Customer Portal and billing webhooks.
Likely data: customer identity/contact fields supplied to Checkout, payment/billing metadata, subscription state and transaction/compliance records. Vexmera stores Stripe customer/subscription identifiers and billing status, not card numbers.
Current legal evidence: Stripe publishes a DPA and describes both processor and controller roles depending on the processing activity, plus a maintained subprocessor/service-provider list.
Launch action: final VAT/tax and live-billing decision remains an owner/accounting/legal gate.

### Resend
Purpose: transactional email delivery through SMTP.
Likely data: recipient email address, transactional message content and delivery metadata.
Current legal evidence: Resend publishes a DPA and a current subprocessor list. Its published list includes infrastructure, monitoring, support and delivery-related providers.
Launch action: confirm the production Vexmera account is covered by the current DPA and document any provider-native message/log retention that affects public policy wording.

## Connected platforms that may be independent controllers and/or processors depending on use

### Google
Purpose: OAuth authentication to permitted Google services, Google Analytics reads and Google Ads read-only reporting during Private Beta; optional Google Analytics on the Vexmera application only after consent.
Likely data: OAuth identifiers/tokens, analytics/reporting metrics, campaign/account metadata and optional site analytics identifiers.
Current product controls: Google/ads-related analytics consent is denied by default for Vexmera site analytics until opt-in; Google Ads external execution remains disabled; disconnect removes Vexmera's local credential and attempts upstream revocation.
Legal review action: map the applicable Google Ads/Analytics terms and controller/processor roles for each distinct flow rather than treating all Google processing as one role.

### Meta
Purpose: OAuth and read-only Meta Ads reporting during Private Beta.
Likely data: OAuth identifiers/tokens, ad-account identifiers and campaign/reporting metrics.
Current product controls: external Meta execution scope is disabled; disconnect removes the local credential and attempts provider-side revocation.

### Instagram
Purpose: OAuth and read-only reporting for professional Instagram Business/Creator accounts during Private Beta.
Likely data: encrypted OAuth tokens, professional-account/page identifiers, username/profile counters and recent media metadata/performance summaries.
Current product controls: Vexmera requests no Instagram publishing scope and performs no content mutations. Local disconnect does not revoke shared Meta permissions because doing so could unintentionally break a separate Meta Ads connection.

### Shopify
Purpose: OAuth and read-only commerce reporting during Private Beta.
Likely data: encrypted access/refresh tokens, shop domain/name/currency, and daily aggregate order count/revenue for the authorized reporting period.
Current product controls: only read_orders is requested; no write scopes are requested. Vexmera aggregates orders in memory and does not persist raw orders, customer names, email addresses or postal addresses.
Legal review action: map the applicable Meta business/data terms and roles for the connected reporting flow.

## Internal data categories and flows

- Account/authentication: email, password hash, sessions, password reset capabilities, workspace invitations.
- Workspace/business context: workspace name, company profile, onboarding profile, brand/business preferences.
- Connector credentials: encrypted OAuth credentials and provider/account identifiers.
- Marketing/reporting: campaign metrics, KPI rows, anomaly records and notifications.
- AI/product: prompts/instructions, generated analyses, runs, approvals, saved settings and product usage events.
- Billing: Stripe customer/subscription identifiers, plan, billing status, trial date and idempotent billing events.
- Email: queued transactional email and delivery context.
- Feedback: beta feedback supplied by users.

## Final legal-review checklist

Before publishing a final subprocessor list or DPA:
1. confirm the exact production account/plan and DPA applicability for Vercel, Neon, OpenAI, Stripe and Resend;
2. capture current processing regions/transfer mechanisms where applicable;
3. confirm provider-native retention that Vexmera cannot directly control;
4. subscribe to subprocessor-change notices where available;
5. determine when Vexmera acts as controller versus processor for business-customer data;
6. keep Google and Meta role descriptions flow-specific;
7. avoid promising deletion from third-party statutory/security records that Vexmera cannot guarantee.
