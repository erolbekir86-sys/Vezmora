from __future__ import annotations

from .store import get_fx_rate, get_workspace_settings


def to_base(workspace_id: int, amount: float, currency: str) -> float:
    settings = get_workspace_settings(workspace_id)
    base = str(settings.get("base_currency") or "SEK").upper()
    quote = currency.upper()
    if quote == base:
        return float(amount)
    rate = get_fx_rate(workspace_id, quote)
    if not rate:
        raise ValueError(f"Missing FX rate from {quote} to {base}")
    return float(amount) * float(rate)


def from_base(workspace_id: int, amount: float, currency: str) -> float:
    settings = get_workspace_settings(workspace_id)
    base = str(settings.get("base_currency") or "SEK").upper()
    quote = currency.upper()
    if quote == base:
        return float(amount)
    rate = get_fx_rate(workspace_id, quote)
    if not rate:
        raise ValueError(f"Missing FX rate from {quote} to {base}")
    return float(amount) / float(rate)
