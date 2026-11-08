# Social connections: owner setup and live verification

Reviewed 2026-11-08. No pilot company has been recruited. No new live provider grant or fresh customer sync is claimed by this change.

## Intended first pilot

Use one invited company and one verified read-only connection. Additional channels can follow later. A free pilot does not require enabling payments, ad execution or content publishing. Final legal/business facts and an authenticated production walkthrough still need approval before onboarding a real company.

## LinkedIn Ads

- Production callback: `https://vexmera.com/api/connectors/linkedin/callback`.
- Missing production settings: `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`.
- Register the callback under the existing Vexmera developer app's authorized redirects. Keep secrets in the hosting secret store, never the repository or chat.
- Request Advertising API access with `r_ads` and `r_ads_reporting`. This connector does not request `rw_ads` or posting permissions.
- Set `LINKEDIN_ADS_API_APPROVED=true` only after checking actual approval. No approval is inferred from key presence.
- Use an ad-account member with reporting access. Save the LinkedIn Ad Account ID under Connections, then authorize and sync. Account settings now survive authorization/reconnection.
- Compare daily impressions, clicks, spend, currency and available conversion metrics against Campaign Manager for the exact period. Exercise empty data, expired access and disconnect separately. Record dated evidence; CI mocks do not prove live access.

Reference: https://learn.microsoft.com/en-us/linkedin/marketing/increasing-access

## Instagram organic reporting

- Production key inventory contains `META_APP_ID`, `META_APP_SECRET`, `INSTAGRAM_REDIRECT_URI`; their secret values were not retrieved. Presence does not prove their correctness or a live grant.
- Required callback: `https://vexmera.com/api/connectors/instagram/callback`.
- Use the existing Meta app, an Instagram Business/Creator account linked to a managed Facebook Page, and a person allowed to authorize that Page.
- Requested permissions: `pages_show_list`, `pages_read_engagement`, `instagram_basic`, `instagram_manage_insights`. No publishing permission is requested.
- Verify the relevant Meta app review/access requirements for external customer accounts. Set `INSTAGRAM_APP_REVIEW_APPROVED=true` only after checking actual approval.
- Grant the intended Instagram account only. Multiple discovered professional accounts are rejected rather than silently selecting the first one.
- The current adapter imports profile counters and recent media/likes/comments summaries, not an attributed sales or advertising report. Follower counts and media likes/comments are current counters, not period deltas.
- Compare username, profile counters and the selected recent-media period with Instagram. Pagination stays on the fixed Graph API origin and an incomplete fetch leaves the previous saved report untouched.

Reference: https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/

## TikTok Ads reporting preview

This is Marketing API reporting, separate from consumer Login Kit, organic TikTok analytics and Content Posting API. No publishing, campaign/budget mutations or payments are implemented.

- Production callback: `https://vexmera.com/api/connectors/tiktok/callback`.
- Still required: a TikTok API for Business developer app, `TIKTOK_APP_ID`, `TIKTOK_APP_SECRET`, and `TIKTOK_AUTHORIZATION_URL` copied from My Apps > Basic Information > Advertiser authorization URL. It must match the configured app ID and callback.
- Configure and obtain approval for reporting-only permissions, including Reporting > Consolidated Report. Do not select campaign-management or publishing permissions. Set `TIKTOK_ADS_API_APPROVED=true` only after the actual app approval and permission selection have been verified.
- The code validates the authorization URL, stores a one-time workspace-bound state and processes `auth_code` server-side. Only required token/authorized-advertiser data is encrypted. Multiple advertisers require explicit selection of an authorized Advertiser ID.
- Reporting uses TikTok's documented v2.0 consolidated report endpoint, at most 30 days of daily data and 20 pages. HTTP/provider errors, duplicate data, unavailable metrics or incomplete pagination do not replace the previous report.
- The interface shows spend, impressions and clicks by currency. Preview data is deliberately excluded from campaign/KPI tables, ROAS, AI recommendations based on those tables and automatic actions until its mapping is reconciled with a real authorized account.
- Local mocked tests prove application behavior only. Token exchange, approved scope selection, endpoint/metric availability and account currency must still be verified live. Reconcile against Ads Manager using a matching report definition; synchronous API and downloadable reports may differ in documented ways. Do not mark this integration pilot-ready on the strength of source code or key presence alone.
- Disconnect removes Vexmera's local token and pending states, while retaining reporting history under the existing explicit privacy controls. Provider-side authorization must be removed in TikTok's authorization settings if upstream revocation is needed.

References:

- https://business-api.tiktok.com/portal/docs/api-reference/v2.0
- https://business-api.tiktok.com/portal/docs/run-a-synchronous-report/v2.0
- https://business-api.tiktok.com/portal/docs?id=1835052398174274

## Evidence required before each channel is marked verified

Record the deployment revision, date, approved account, requested/read-only permissions, OAuth result, selected workspace/account, sync period, source comparison, expected empty/expired-access behavior and disconnect result. Never store tokens or customer reporting screenshots in the public repository. Keep proof summaries and access-controlled links in the private development planner.
