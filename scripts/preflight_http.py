from __future__ import annotations

from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

_MAX_PUBLIC_RESPONSE_BYTES = 1_048_576


class _NoRedirectHandler(HTTPRedirectHandler):
    """Keep pilot evidence bound to the exact origin/path requested."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def normalize_https_origin(base_url: str) -> str:
    """Return a plain HTTPS origin or reject ambiguous/operator-unsafe input."""
    raw = str(base_url or "").strip()
    try:
        parsed = urlsplit(raw)
        _ = parsed.port
    except ValueError as exc:
        raise ValueError("base_url must be a valid HTTPS origin") from exc

    if (
        parsed.scheme.lower() != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise ValueError("base_url must be a plain HTTPS origin")

    return f"https://{parsed.netloc.lower()}"


def get_public_text(
    url: str,
    *,
    user_agent: str,
    timeout: float = 8.0,
    max_bytes: int = _MAX_PUBLIC_RESPONSE_BYTES,
) -> tuple[int, str]:
    """GET one public preflight target without redirects or unbounded buffering."""
    request = Request(url, headers={"User-Agent": user_agent})
    opener = build_opener(_NoRedirectHandler())
    try:
        with opener.open(request, timeout=timeout) as response:
            body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                raise RuntimeError("response_too_large")
            return int(response.status), body.decode("utf-8", errors="replace")
    except HTTPError as exc:
        return int(exc.code), ""
    except (URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"request_failed:{type(exc).__name__}") from exc
