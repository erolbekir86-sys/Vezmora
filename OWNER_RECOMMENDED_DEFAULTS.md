# Vexmera owner decision defaults

Last updated: 2026-09-15

Purpose: reduce the remaining owner/legal decisions to a short review. This is a commercial/legal decision brief, not final legal advice and not public Terms.

## Recommended Private Beta posture

- Customer scope: B2B only during Private Beta.
- Geography: Sweden first; other EU business customers only after VAT/accounting flow is verified.
- Billing: Stripe test/sandbox only until the legal entity, VAT status, invoicing details and public Terms are approved.
- Ads/integrations: read-only Google/Meta during pilot; no live ad execution, budget or bid changes.

## VAT / tax recommendation

- Swedish taxable sales: use the Swedish standard VAT rate when applicable. The Swedish standard rate is currently 25%.
- EU B2B services: support reverse-charge treatment only when the customer is a taxable business and the relevant conditions, including valid VAT details, are satisfied.
- Do not infer VAT treatment solely from country. Capture and validate the customer legal entity/country/VAT number before live billing.
- Keep displayed SaaS plan prices clearly marked as excluding VAT for B2B if that remains the intended commercial model.
- Final VAT/accounting implementation should be checked against the actual Vexmera legal entity and accountant setup before live paid launch.

Official basis reviewed 2026-09-15: Skatteverket states that Sweden's normal VAT rate is 25%, and that cross-border B2B services within the EU may use reverse-charge treatment when the applicable conditions are met.

## Governing law / dispute recommendation

Recommended default for a Sweden-first B2B Private Beta:
- governing law: Swedish law;
- dispute venue: competent Swedish court;
- do not hard-code a specific district court until the legal entity/registered address and legal review are complete.

## Cancellation / refund recommendation

Recommended B2B SaaS default:
- subscriptions may be cancelled for the end of the current billing period;
- no automatic pro-rata refund for an already-started billing period unless required by applicable law or specifically agreed;
- duplicate or erroneous charges should be corrected/refunded;
- Beta credits or discretionary refunds may be granted by Vexmera without creating a general entitlement.

Do not publish this as final policy until billing/legal review confirms that it matches the intended customer contracts and Stripe configuration.

## Liability recommendation

Recommended negotiation starting point for B2B Private Beta, subject to legal review:
- exclude indirect/consequential losses to the extent legally permitted;
- do not promise uninterrupted or error-free Beta service;
- make customers responsible for reviewing recommendations before business decisions;
- preserve liability that cannot legally be excluded;
- use an aggregate liability cap tied to fees paid/payable over a defined prior period, but leave the exact cap and period for final legal approval.

Do not insert an arbitrary numeric liability cap into public Terms without legal review.

## Data / privacy recommendation

- Use the already prepared implementation-aligned retention schedule as the default proposal.
- Keep data minimisation and deletion controls enabled.
- Keep processors/subprocessors disclosed based on actual production use, not planned integrations.
- Do not claim a processor DPA/subprocessor status until the relevant account/contract has been checked.

## Remaining facts only the owner can supply

1. Exact legal entity/business name.
2. Organisation/registration number, if applicable.
3. Registered/postal address.
4. Official `@vexmera.com` privacy/support address.
5. Whether the first external pilot is strictly B2B.
6. Final legal approval of governing law/dispute/liability/refund wording.
7. Confirmation of VAT registration/accounting treatment for live billing.

## Suggested approval shorthand

If the owner agrees with the commercial defaults above, the practical response can be reduced to:

- B2B-only pilot: YES / NO
- Swedish law: YES / REVIEW
- Cancel at period end: YES / REVIEW
- No automatic pro-rata refund after period starts: YES / REVIEW
- Liability approach above: YES / REVIEW
- Retention proposal: YES / CHANGES
- Live billing remains OFF until VAT/legal facts complete: YES / NO
