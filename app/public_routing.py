from __future__ import annotations

import os
import re
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.routing import APIRoute

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
CANONICAL_ORIGIN = "https://vexmera.com"
PRODUCT_QUERY_KEYS = frozenset({"reset", "invite", "billing"})

_raw_build_id = (os.getenv("VERCEL_GIT_COMMIT_SHA") or "local").strip()
BUILD_ID = re.sub(r"[^A-Za-z0-9._-]", "", _raw_build_id)[:16] or "local"
_STATIC_ASSET_RE = re.compile(r'(?P<prefix>(?:src|href)=["\'])(?P<url>/static/[^"\']+)')
_FOOTER_LINK_RE = re.compile(
    r'<a\s+href="[^"]*"(?P<attrs>[^>]*)data-i18n="footer\.(?P<kind>privacy|terms)"(?P<tail>[^>]*)>',
    re.IGNORECASE,
)


NO_STORE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
    "CDN-Cache-Control": "no-store",
    "Vercel-CDN-Cache-Control": "no-store",
}


def _inject_before_head_end(html: str, fragment: str) -> str:
    if fragment.strip() in html:
        return html
    return html.replace("</head>", f"{fragment}\n</head>", 1)


def _version_static_assets(html: str) -> str:
    """Cache-bust every local frontend asset with the current deployment id."""

    def replace(match: re.Match[str]) -> str:
        url = match.group("url")
        separator = "&" if "?" in url else "?"
        return f'{match.group("prefix")}{url}{separator}build={BUILD_ID}'

    return _STATIC_ASSET_RE.sub(replace, html)


def _link_public_legal_pages(html: str) -> str:
    """Point existing translated footer links at the public legal pages."""

    def replace(match: re.Match[str]) -> str:
        kind = match.group("kind").lower()
        path = "/privacy" if kind == "privacy" else "/terms"
        return (
            f'<a href="{path}"{match.group("attrs")}data-i18n="footer.{kind}"'
            f'{match.group("tail")}>'
        )

    return _FOOTER_LINK_RE.sub(replace, html)


def install_public_routing(app: FastAPI) -> None:
    """Expose the marketing site at `/` and keep the authenticated product at `/app`.

    The installer is intentionally idempotent because the package is imported by
    both local tests and the Vercel entrypoint.
    """
    if getattr(app.state, "vexmera_public_routing_installed", False):
        return

    # app.main historically owns GET /. Remove only that exact product-shell
    # route and leave every API/static/docs route untouched.
    app.router.routes[:] = [
        route
        for route in app.router.routes
        if not (
            isinstance(route, APIRoute)
            and route.path == "/"
            and "GET" in (route.methods or set())
        )
    ]

    async def marketing_home(request: Request) -> Response:
        # Existing private-beta email, invite, and Stripe return links were built
        # against the old product-at-root layout. Preserve those links while the
        # canonical base URL remains the apex domain.
        if PRODUCT_QUERY_KEYS.intersection(request.query_params.keys()):
            target = "/app"
            if request.url.query:
                target = f"{target}?{request.url.query}"
            return RedirectResponse(target, status_code=302)

        html = (STATIC / "landing.html").read_text(encoding="utf-8")
        # The landing page was originally shipped beside the app while `/`
        # pointed to login. Keep all existing CTA copy/design, but send those
        # root links to the authenticated product route now.
        html = html.replace('href="/"', 'href="/app"')
        html = _link_public_legal_pages(html)
        seo = (
            f'  <link rel="canonical" href="{CANONICAL_ORIGIN}/" />\n'
            '  <meta name="robots" content="index,follow" />\n'
            '  <meta property="og:type" content="website" />\n'
            '  <meta property="og:site_name" content="Vexmera" />\n'
            '  <meta property="og:title" content="Vexmera — AI Marketing Officer" />\n'
            '  <meta property="og:description" content="Förstå din marknadsföring, se vad som driver resultat och vet vad du ska göra härnäst." />\n'
            f'  <meta property="og:url" content="{CANONICAL_ORIGIN}/" />\n'
            '  <meta name="twitter:card" content="summary_large_image" />\n'
            '  <style id="landing-reveal-failsafe">\n'
            '    html,body{visibility:visible!important;opacity:1!important}\n'
            '    .reveal{opacity:1!important;transform:none!important;filter:none!important}\n'
            '  </style>\n'
            '  <script>document.documentElement.classList.remove("vexmera-reveal-js");'
            f'window.__VEXMERA_BUILD__="{BUILD_ID}";</script>\n'
            '  <link rel="preload" as="image" href="/static/vexmera-founder.jpg" fetchpriority="high" />\n'
            '  <link rel="stylesheet" href="/static/landing-ux.css" />\n'
            '  <link rel="stylesheet" href="/static/landing-refine.css" />\n'
            '  <link rel="stylesheet" href="/static/landing-icon-premium.css" />\n'
            '  <link rel="stylesheet" href="/static/landing-section-art.css" />\n'
            '  <link rel="stylesheet" href="/static/landing-section-art-data.css" />\n'
            '  <link rel="stylesheet" href="/static/landing-section-art-decision.css" />\n'
            '  <link rel="stylesheet" href="/static/landing-section-art-how.css" />\n'
            '  <link rel="stylesheet" href="/static/landing-section-art-workflow.css" />\n'
            '  <link rel="stylesheet" href="/static/landing-section-art-security.css" />\n'
            '  <script src="/static/founder-photo-fix.js" defer></script>\n'
            '  <script src="/static/landing-runtime-safe.js" defer></script>\n'
            '  <script src="/static/landing-refine.js" defer></script>\n'
            '  <script src="/static/landing-section-art.js" defer></script>'
        )
        html = _inject_before_head_end(html, seo)
        # Load the visual premium layer after landing.js so it cannot be
        # overwritten by the landing script's dynamically appended CSS layers.
        # The icon pass runs last and uses bounded retries so late-injected
        # conversion cards receive the same icon system without a permanent observer.
        html = html.replace(
            '<script src="/static/landing.js" defer></script>',
            '<script src="/static/landing.js" defer></script>\n'
            '  <script src="/static/landing-premium.js" defer></script>\n'
            '  <script src="/static/landing-icon-premium.js" defer></script>',
            1,
        )
        html = _version_static_assets(html)
        return HTMLResponse(html, headers=NO_STORE_HEADERS)

    async def privacy_policy() -> HTMLResponse:
        html = (STATIC / "privacy.html").read_text(encoding="utf-8")
        return HTMLResponse(html, headers=NO_STORE_HEADERS)

    async def terms_of_service() -> HTMLResponse:
        html = (STATIC / "terms.html").read_text(encoding="utf-8")
        return HTMLResponse(html, headers=NO_STORE_HEADERS)

    async def product_shell() -> HTMLResponse:
        html = (STATIC / "index.html").read_text(encoding="utf-8")
        # The original app polish helper observes the whole dynamic product DOM.
        # Use the stability-first one-shot helper in production so parallel app
        # bootstrap updates cannot create a mutation storm and freeze the tab.
        html = html.replace(
            '<script src="/static/app-polish.js?v=1"></script>',
            '<script src="/static/app-polish-safe.js"></script>',
        )
        # Keep the legacy app bundle unchanged while enforcing fail-closed onboarding
        # saves, fail-closed dashboard reads and current self-service pricing as
        # small, reversible beta hardening layers loaded immediately after it.
        html = html.replace(
            '<script src="/static/app.js"></script>',
            '<script src="/static/app.js"></script>\n'
            '  <script src="/static/onboarding-save-guard.js"></script>\n'
            '  <script src="/static/dashboard-read-guard.js"></script>\n'
            '  <script src="/static/self-service-alignment.js"></script>',
            1,
        )
        html = _inject_before_head_end(
            html,
            f'  <meta name="robots" content="noindex,nofollow" />\n'
            f'  <script>window.__VEXMERA_BUILD__="{BUILD_ID}";</script>',
        )
        html = _version_static_assets(html)
        return HTMLResponse(
            html,
            headers={
                **NO_STORE_HEADERS,
                "X-Robots-Tag": "noindex, nofollow",
            },
        )

    async def robots() -> PlainTextResponse:
        body = (
            "User-agent: *\n"
            "Allow: /\n"
            "Allow: /privacy\n"
            "Allow: /terms\n"
            "Disallow: /app\n"
            "Disallow: /api/\n"
            "Disallow: /health\n"
            "Disallow: /static/landing.html\n"
            f"Sitemap: {CANONICAL_ORIGIN}/sitemap.xml\n"
        )
        return PlainTextResponse(body)

    async def sitemap() -> Response:
        body = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            "  <url>\n"
            f"    <loc>{CANONICAL_ORIGIN}/</loc>\n"
            "    <changefreq>weekly</changefreq>\n"
            "    <priority>1.0</priority>\n"
            "  </url>\n"
            "  <url>\n"
            f"    <loc>{CANONICAL_ORIGIN}/privacy</loc>\n"
            "    <changefreq>monthly</changefreq>\n"
            "    <priority>0.5</priority>\n"
            "  </url>\n"
            "  <url>\n"
            f"    <loc>{CANONICAL_ORIGIN}/terms</loc>\n"
            "    <changefreq>monthly</changefreq>\n"
            "    <priority>0.4</priority>\n"
            "  </url>\n"
            "</urlset>\n"
        )
        return Response(content=body, media_type="application/xml")

    app.add_api_route(
        "/",
        marketing_home,
        methods=["GET"],
        include_in_schema=False,
        name="marketing_home",
    )
    app.add_api_route(
        "/privacy",
        privacy_policy,
        methods=["GET"],
        include_in_schema=False,
        name="privacy_policy",
    )
    app.add_api_route(
        "/privacy/",
        privacy_policy,
        methods=["GET"],
        include_in_schema=False,
        name="privacy_policy_slash",
    )
    app.add_api_route(
        "/terms",
        terms_of_service,
        methods=["GET"],
        include_in_schema=False,
        name="terms_of_service",
    )
    app.add_api_route(
        "/terms/",
        terms_of_service,
        methods=["GET"],
        include_in_schema=False,
        name="terms_of_service_slash",
    )
    app.add_api_route(
        "/app",
        product_shell,
        methods=["GET"],
        include_in_schema=False,
        name="product_shell",
    )
    app.add_api_route(
        "/app/",
        product_shell,
        methods=["GET"],
        include_in_schema=False,
        name="product_shell_slash",
    )
    app.add_api_route(
        "/robots.txt",
        robots,
        methods=["GET"],
        include_in_schema=False,
        name="robots_txt",
    )
    app.add_api_route(
        "/sitemap.xml",
        sitemap,
        methods=["GET"],
        include_in_schema=False,
        name="sitemap_xml",
    )

    app.state.vexmera_public_routing_installed = True
