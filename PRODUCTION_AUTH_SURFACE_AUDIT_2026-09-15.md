# Vexmera production auth-surface audit — 2026-09-15

## Scope
Unauthenticated verification against production `https://vexmera.com` after the Private Beta legal/readiness merge.

## Public app shell
`/app` returns the unauthenticated login/register shell only. The authenticated application shell is hidden before login. The response is protected with `no-store`, `noindex`, HSTS, CSP, frame denial and other hardening headers.

## Read API checks
The following unauthenticated requests were tested against production with a synthetic workspace id and all returned HTTP 401 instead of workspace data:

- `GET /api/workspaces`
- `GET /api/company?workspace_id=1`
- `GET /api/briefs/latest?workspace_id=1`
- `GET /api/connectors?workspace_id=1`
- `GET /api/notifications?workspace_id=1`
- `GET /api/kpis?workspace_id=1`
- `GET /api/team?workspace_id=1`

Expected result: `401 Authentication required` or equivalent fail-closed response.

## What this proves
These checks provide production evidence that representative workspace-scoped read surfaces do not expose customer/workspace data to an unauthenticated visitor.

## What this does not prove
This is not a replacement for authenticated cross-workspace authorization QA. Before the five-company pilot is considered fully manually verified, the browser QA should still confirm that a logged-in user cannot read another workspace by changing IDs and that role restrictions remain correct for owner/admin/marketer/viewer where applicable.

## Public legal surface observation
`/privacy` is currently Swedish while `/terms` is currently English. This is not an access-control defect, but it is a language-consistency item for the Swedish pilot. A Swedish Terms publication draft is maintained separately and deliberately keeps unresolved legal owner decisions explicit rather than copying unverified definitive claims from the existing public Terms page.

## Status
- Unauthenticated representative read API boundary: GREEN
- Public app shell cache/index/security posture: GREEN
- Authenticated cross-workspace browser evidence: ORANGE, manual/browser evidence still required
- Swedish public Terms publication: ORANGE pending owner/legal sign-off
