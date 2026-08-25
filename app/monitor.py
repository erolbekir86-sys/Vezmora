from __future__ import annotations

import hashlib
import html
import ipaddress
import re
import socket
from urllib.parse import urlparse

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


def _safe_public_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    host = parsed.hostname.lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        return False
    try:
        ip = ipaddress.ip_address(host)
        return not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved)
    except ValueError:
        pass
    try:
        for info in socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return False
    except socket.gaierror:
        pass
    return True


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
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True, max_redirects=4) as client:
            response = await client.get(url, headers=headers)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Competitor page could not be fetched") from exc
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Competitor page returned HTTP {response.status_code}")
    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type.lower():
        raise HTTPException(status_code=415, detail="Competitor monitor currently supports HTML pages only")
    title, excerpt, digest = normalize_page(response.text[:2_000_000])
    previous = latest_competitor_snapshot(competitor_id)
    changed = bool(previous and previous.get("content_hash") != digest)
    snapshot_id = add_competitor_snapshot(workspace_id, competitor_id, digest, title, excerpt, response.status_code, changed)
    if changed:
        add_notification(
            workspace_id, "rival_change", f"{competitor['name']} changed",
            "Vezmora detected a meaningful page-content hash change. Review the site before reacting.",
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
