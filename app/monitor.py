from __future__ import annotations

import hashlib
import html
import ipaddress
import re
import socket
from urllib.parse import urljoin, urlparse

import httpx
from fastapi import HTTPException

from .store import (
    add_competitor_snapshot,
    add_notification,
    get_competitor,
    latest_competitor_snapshot,
    list_competitors,
)

_TAG_RE = re.compile(r"<[^>]+>")
_SCRIPT_RE = re.compile(r"<(script|style|noscript)[^>]*>.*?</\1>", re.I | re.S)
_SPACE_RE = re.compile(r"\s+")
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
_REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})
_MAX_REDIRECTS = 4
_MAX_RESPONSE_BYTES = 2_000_000


def _safe_public_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    # Userinfo in a URL can accidentally turn saved competitor URLs or
    # redirects into credential-bearing requests. The monitor never needs it.
    if parsed.username is not None or parsed.password is not None:
        return False
    host = parsed.hostname.lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        return False
    try:
        return ipaddress.ip_address(host).is_global
    except ValueError:
        pass
    try:
        for info in socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM):
            if not ipaddress.ip_address(info[4][0]).is_global:
                return False
    except socket.gaierror:
        return False
    return True


def _declared_response_too_large(response: httpx.Response) -> bool:
    raw = response.headers.get("content-length")
    if not raw:
        return False
    try:
        return int(raw) > _MAX_RESPONSE_BYTES
    except (TypeError, ValueError):
        return False


async def _buffer_bounded_response(response: httpx.Response) -> httpx.Response:
    if _declared_response_too_large(response):
        raise HTTPException(status_code=413, detail="Competitor page is too large to scan")

    body = bytearray()
    async for chunk in response.aiter_bytes():
        if len(body) + len(chunk) > _MAX_RESPONSE_BYTES:
            raise HTTPException(status_code=413, detail="Competitor page is too large to scan")
        body.extend(chunk)

    return httpx.Response(
        response.status_code,
        headers=response.headers,
        content=bytes(body),
        request=response.request,
        extensions=response.extensions,
    )


async def _fetch_public_page(url: str, headers: dict[str, str]) -> httpx.Response:
    """Fetch one bounded public page while validating every redirect target.

    Automatic redirects are intentionally disabled. A public competitor URL can
    otherwise redirect Vexmera to localhost, link-local metadata services or
    another private address after the initial SSRF check has already passed.
    The final response is streamed and capped so a remote site cannot force the
    serverless worker to buffer an arbitrarily large page in memory.
    """
    current_url = url
    async with httpx.AsyncClient(timeout=15, follow_redirects=False) as client:
        for redirect_count in range(_MAX_REDIRECTS + 1):
            if not _safe_public_url(current_url):
                raise HTTPException(status_code=400, detail="Only public HTTP/HTTPS competitor URLs can be scanned")
            try:
                async with client.stream("GET", current_url, headers=headers) as response:
                    if response.status_code not in _REDIRECT_STATUSES:
                        return await _buffer_bounded_response(response)

                    location = response.headers.get("location")
                    if not location:
                        raise HTTPException(status_code=502, detail="Competitor page returned an invalid redirect")
                    if redirect_count >= _MAX_REDIRECTS:
                        raise HTTPException(status_code=502, detail="Competitor page redirected too many times")

                    next_url = urljoin(str(response.url), location)
                    if not _safe_public_url(next_url):
                        raise HTTPException(status_code=400, detail="Competitor page redirected to a non-public URL")
                    current_url = next_url
            except httpx.HTTPError as exc:
                raise HTTPException(status_code=502, detail="Competitor page could not be fetched") from exc

    raise HTTPException(status_code=502, detail="Competitor page redirected too many times")


def normalize_page(html_text: str) -> tuple[str | None, str, str]:
    title_match = _TITLE_RE.search(html_text)
    title = html.unescape(_SPACE_RE.sub(" ", _TAG_RE.sub(" ", title_match.group(1))).strip()) if title_match else None
    body = _SCRIPT_RE.sub(" ", html_text)
    body = html.unescape(_TAG_RE.sub(" ", body))
    body = _SPACE_RE.sub(" ", body).strip()
    digest = hashlib.sha256(body.encode("utf-8", errors="ignore")).hexdigest()
    return title, body[:700], digest


async def scan_competitor(workspace_id: int, competitor_id: int) -> dict[str, object]:
    competitor = get_competitor(workspace_id, competitor_id)
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    url = competitor.get("url")
    if not url:
        raise HTTPException(status_code=409, detail="Competitor has no website URL")
    if not _safe_public_url(url):
        raise HTTPException(status_code=400, detail="Only public HTTP/HTTPS competitor URLs can be scanned")
    headers = {"User-Agent": "VezmoraBot/0.4 (+competitive-monitor; respectful single-page checks)"}
    response = await _fetch_public_page(url, headers)
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Competitor page returned HTTP {response.status_code}")
    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type.lower():
        raise HTTPException(status_code=415, detail="Competitor monitor currently supports HTML pages only")
    title, excerpt, digest = normalize_page(response.text)
    previous = latest_competitor_snapshot(competitor_id)
    changed = bool(previous and previous.get("content_hash") != digest)
    snapshot_id = add_competitor_snapshot(workspace_id, competitor_id, digest, title, excerpt, response.status_code, changed)
    if changed:
        add_notification(
            workspace_id, "rival_change", f"{competitor['name']} changed",
            "Vexmera detected a meaningful page-content hash change. Review the site before reacting.",
            {"competitor_id": competitor_id, "snapshot_id": snapshot_id, "url": url},
        )
    return {"competitor_id": competitor_id, "name": competitor["name"], "changed": changed, "title": title, "http_status": response.status_code, "snapshot_id": snapshot_id}


async def scan_all_competitors(workspace_id: int) -> list[dict[str, object]]:
    results = []
    for competitor in list_competitors(workspace_id):
        if not competitor.get("url"):
            continue
        try:
            results.append(await scan_competitor(workspace_id, int(competitor["id"])))
        except HTTPException as exc:
            results.append({"competitor_id": competitor["id"], "name": competitor["name"], "error": str(exc.detail), "status": exc.status_code})
    return results
