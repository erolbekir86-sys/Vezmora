from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.routing import APIRoute

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
CANONICAL_ORIGIN = "https://vexmera.com"
PRODUCT_QUERY_KEYS = frozenset({"reset", "invite", "billing"})


def _inject_before_head_end(html: str, fragment: str) -> str:
    if fragment.strip() in html:
        return html
    return html.replace("</head>", f"{fragment}\n</head>", 1)


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

    async def marketing_home(request: Request) -> HTMLResponse | RedirectResponse:
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
        seo = (
            f'  <link rel="canonical" href="{CANONICAL_ORIGIN}/" />\n'
            '  <meta name="robots" content="index,follow" />\n'
            '  <meta property="og:type" content="website" />\n'
            '  <meta property="og:site_name" content="Vexmera" />\n'
            '  <meta property="og:title" content="Vexmera — AI Marketing Officer" />\n'
            '  <meta property="og:description" content="Förstå din marknadsföring, se vad som driver resultat och vet vad du ska göra härnäst." />\n'
            f'  <meta property="og:url" content="{CANONICAL_ORIGIN}/" />\n'
            '  <meta name="twitter:card" content="summary_large_image" />'
        )
        html = _inject_before_head_end(html, seo)
        return HTMLResponse(html, headers={"Cache-Control": "public, max-age=300"})

    async def product_shell() -> HTMLResponse:
        html = (STATIC / "index.html").read_text(encoding="utf-8")
        html = _inject_before_head_end(
            html,
            '  <meta name="robots" content="noindex,nofollow" />',
        )
        return HTMLResponse(
            html,
            headers={
                "Cache-Control": "no-store",
                "X-Robots-Tag": "noindex, nofollow",
            },
        )

    async def robots() -> PlainTextResponse:
        body = (
            "User-agent: *\n"
            "Allow: /\n"
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
