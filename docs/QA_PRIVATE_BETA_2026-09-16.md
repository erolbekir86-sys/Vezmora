# Private Beta authenticated QA — 2026-09-16

A synthetic production account was used to verify registration, login/logout/re-login, onboarding, routing/navigation, dashboard, company profile, Team/Billing read surfaces, account-deletion preview, connector empty states, and recommendation-only execution posture without connecting Google/Meta or entering payment data.

The production billing UI rendered the current Start/Growth/Pro catalog at 995/1495/2995 SEK per month excluding VAT. The authenticated billing API reported Checkout ready for the synthetic workspace before the stricter exact-catalog gate in the accompanying change.

The app source includes a mobile menu toggle and responsive breakpoints, but an explicit real 390x844 browser walkthrough remains evidence to collect before calling mobile QA fully green.

No real advertising, budgets, bids, DNS, bank/KYC or live billing settings were changed.
