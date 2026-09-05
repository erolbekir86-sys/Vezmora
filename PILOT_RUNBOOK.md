# Vexmera private beta pilot runbook

This runbook standardizes onboarding for the first five pilot companies. It is intentionally conservative: Vexmera should analyze and recommend, not autonomously change live advertising.

Use `PILOT_SESSION_TEMPLATE.md` for each company so the five sessions can be compared consistently without collecting secrets.

## Before inviting a pilot

- Production deployment is healthy.
- The public marketing page loads at `https://vexmera.com/` and the authenticated product shell loads at `https://vexmera.com/app`.
- Pilot invitations and onboarding instructions point customers to `https://vexmera.com/app`, not the marketing root.
- `VEZMORA_EXECUTION_ENABLED=false`.
- `VEZMORA_AUTOPILOT_EXECUTION_ENABLED=false`.
- Google/Meta connectors required by the pilot are configured.
- Privacy Policy and Beta Terms have been reviewed and finalized from the current drafts.
- The workspace base currency is correct.

## Pilot onboarding flow

1. Open `https://vexmera.com/app` and create or invite the customer to a workspace.
2. Complete Brand Memory / onboarding with company, market, audience, offer, goal and marketing problem.
3. Connect only the data sources the customer actually uses.
4. Save the relevant Google Analytics property, Google Ads customer ID or Meta Ad Account ID.
5. Run a 30-day sync first.
6. Confirm the result clearly distinguishes one of these states:
   - data synced successfully;
   - connected account is valid but has no campaigns/data;
   - setup or permission action is required;
   - temporary provider/API failure.
7. Generate Core/Pulse recommendations only after the available data state is understood.
8. Record one concrete, evidence-backed recommended next action for the customer.

Existing password-reset, invite and billing-return links that arrive at the root domain are intentionally forwarded into `/app`. Do not rewrite or manually alter their query parameters during a pilot session.

## What counts as a successful pilot session

- Customer can reach the authenticated product from the onboarding instructions without founder navigation help.
- Customer can understand what Vexmera connected to.
- At least one real data source syncs when data exists.
- Empty accounts are described as empty, not broken.
- Errors do not expose OAuth tokens, developer tokens, API keys or secrets.
- AI output distinguishes observed facts from assumptions.
- No campaign, budget, bid or ad is changed automatically.

## Founder support notes

For each pilot, record:

- time needed to onboard;
- steps where the customer needed help;
- connector used;
- sync outcome;
- first useful recommendation;
- confusing labels or screens;
- errors encountered;
- whether the customer would use the product again without assistance.

Record these in `PILOT_SESSION_TEMPLATE.md` rather than free-form notes where possible. Do not paste credentials, OAuth tokens, developer tokens, API keys, authorization headers, payment information, or raw provider payloads containing secrets into pilot notes.

## Exit criteria for the five-company pilot

The pilot phase is complete when five businesses have attempted onboarding and the team can answer:

1. Can a new business reach useful data with minimal help?
2. Does Vexmera explain missing/empty data clearly?
3. Are recommendations grounded in real customer data where available?
4. Are failures diagnosable without asking customers for secrets?
5. Is there a repeated use case customers value enough to return for?

Do not enable autonomous external execution as part of this pilot.
