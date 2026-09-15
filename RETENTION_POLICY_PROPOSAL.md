# Vexmera retention policy proposal

Last reviewed: 2026-09-15

Status: engineering/legal proposal for Private Beta. This document separates implemented retention from proposed longer-lived retention. Final public wording still requires owner/legal approval.

## Verified implemented retention

- Sessions expire after 14 days. Expired rows are pruned opportunistically and active sessions are capped at 20 per user.
- Password-reset capabilities expire after 60 minutes. A new reset request invalidates older reset capabilities for the same account; expired rows are pruned.
- Workspace invites expire after 7 days. A new invite to the same email/workspace supersedes an older outstanding invite; expired rows are pruned.
- Google/Meta connector credentials are removed locally when the supported disconnect flow completes; provider-side revocation is best-effort.
- Synchronized reporting history can be deleted separately by an authorized workspace owner/admin. This removes synced campaign metrics, imported provider KPI rows, anomalies and anomaly notifications while preserving manually entered KPI rows.
- Eligible self-service account deletion removes the local user account, solo-owned workspaces and their cascaded local data after blocker checks and re-authentication. Shared workspaces owned by others remain.
- Neon point-in-time recovery/history is currently configured to 6 hours. This is infrastructure recovery state, not a promise that every processor keeps data for exactly six hours.

## Proposed longer-lived retention for Private Beta

These periods are deliberately conservative and should be reviewed before publication:

- Active account/workspace data: for the duration of the customer relationship, then 30 days after account closure unless earlier deletion is requested and no legal/security hold applies.
- Company/brand profile and manually entered workspace content: same as account/workspace data.
- Synchronized campaign and analytics data: rolling 24 months while the workspace is active, with earlier deletion available through the synchronized-history deletion control. For the five-company pilot, retaining only what is operationally useful is preferred.
- AI prompts, generated analyses and saved AI context: 90 days by default for operational continuity, unless a shorter period is technically configured or the customer deletes the underlying account/workspace earlier. Do not publicly promise this until the actual storage path is verified end to end.
- Competitor records and snapshots: rolling 12 months while active, then delete with the workspace. Shorter retention is acceptable if product utility remains intact.
- Product usage events and non-security diagnostics: 90 days.
- Security and abuse logs: 180 days where available and proportionate, subject to provider-native retention and incident needs.
- Beta feedback tied to an identifiable user: 12 months after beta participation ends, then anonymize or delete unless needed to resolve a dispute.
- Transactional email application records: 30 days in Vexmera where technically feasible; provider-held delivery metadata follows the email provider's verified service terms and retention.
- Billing/subscription records in Vexmera: retain while the subscription/account relationship is active, then 24 months for operational dispute/reconciliation purposes unless applicable accounting/tax law requires longer. Stripe-held records follow Stripe's own legal obligations and roles.
- Legal/accounting/tax records: retain for the statutory period applicable to the final operator entity and jurisdiction. This period must be set by the owner/accountant/legal reviewer, not guessed in product code.
- Database recovery copies/backups: follow the verified infrastructure configuration and provider controls. Current Neon project recovery history is 6 hours; do not generalize this to all processors.

## Deletion precedence

A valid deletion request should override the proposed product-retention window unless data must be kept for security, fraud prevention, billing/accounting, disputes or another legal obligation. Processor-side deletion is not guaranteed to be instantaneous and must be described according to the provider's verified terms.

## Engineering follow-up

Before these proposed periods become public commitments, engineering must verify or implement scheduled deletion for every category that is given a concrete period. Until then, Privacy Policy wording should distinguish implemented short-lived capability retention from proposed longer-lived product-data retention.
