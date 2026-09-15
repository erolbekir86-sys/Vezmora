# Public Terms gap audit — 2026-09-15

The current production `/terms` page is functional and accessible, but it is more definitive than the current legal-review status supports. Before the Swedish Terms draft replaces or supplements the public page, the following statements should be explicitly confirmed by the owner/legal review.

## Items requiring confirmation
1. **Contracting party** — current public Terms use the brand name Vexmera without identifying the legal operator/entity.
2. **Contact address** — current public Terms use `vexmera.platform@gmail.com`; the Private Beta readiness plan calls for a verified official `@vexmera.com` support/privacy/legal channel.
3. **Refund wording** — current public Terms state that paid fees are generally non-refundable except where law requires otherwise. This should match the final B2B policy and Stripe configuration before live billing.
4. **Taxes/VAT** — current public Terms say applicable taxes will be presented, but the final Swedish/EU VAT treatment has not yet been owner-approved for live billing.
5. **Governing law/forum** — current public Terms definitively select Swedish law and competent Swedish courts. The newer legal-readiness drafts intentionally keep this as an owner/legal decision until confirmed.
6. **Liability** — current public Terms exclude broad categories of indirect/consequential loss without a fully reviewed aggregate liability structure. Final wording should be legally reviewed for the intended B2B pilot/customer relationship.
7. **Live-paid-service language** — the current Terms discuss paid services generally while production billing remains in test mode for launch-readiness purposes. Public wording should not imply that live billing has already been approved/enabled.

## Language consistency
- `/privacy`: Swedish
- `/terms`: English

For a Sweden-first Private Beta, a Swedish Terms version is prepared in `SWEDISH_TERMS_DRAFT.md`, but should remain a draft until the unresolved owner/legal items are filled in.

## Recommendation
Do not silently translate the current English Terms verbatim. First confirm the seven items above, then publish a Swedish version whose promises match the actual product, Stripe configuration and operator identity.
