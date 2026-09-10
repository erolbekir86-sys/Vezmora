from __future__ import annotations

from functools import wraps

from . import store as _store
from .secret_redaction import redact_sensitive_text

_ORIGINAL_FINISH_EMAIL = _store.finish_email


@wraps(_ORIGINAL_FINISH_EMAIL)
def finish_email_with_body_scrub(email_id: int, error: str | None = None) -> None:
    """Sanitize delivery errors and erase body text after successful delivery.

    Transactional email bodies can contain one-time invite or password-reset URLs.
    Once SMTP delivery succeeds, Vexmera no longer needs that body in its outbox
    audit row. Failed messages retain their body so a future explicit retry flow
    can still be implemented without silently discarding undelivered content.
    """
    safe_error = redact_sensitive_text(error) if error else error
    _ORIGINAL_FINISH_EMAIL(email_id, safe_error)
    if error:
        return

    with _store._connect() as con:
        con.execute(
            "UPDATE email_outbox SET body_text='' WHERE id=? AND status='sent'",
            (email_id,),
        )


def install_email_outbox_privacy() -> None:
    """Install email outbox privacy handling before emailer.py binds store.finish_email."""
    if getattr(_store, "_vexmera_email_outbox_privacy_installed", False):
        return
    _store.finish_email = finish_email_with_body_scrub
    _store._vexmera_email_outbox_privacy_installed = True
