# Private Beta CSRF origin hardening

This change makes browser mutation protection fail closed when `VEZMORA_APP_URL` is configured but malformed.

Covered malformed canonical origins include values with credentials, paths, query strings, or fragments. When the variable is omitted entirely, local and test environments retain the existing request-origin fallback.

The regression tests cover both unauthenticated auth POSTs and authenticated browser mutations. No DNS, credentials, secrets, external account permissions, ad execution, budgets, bids, or payment settings are changed.
