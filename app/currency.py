from __future__ import annotations

from fastapi import HTTPException

from .store import get_fx_rate, get_workspace_settings


def base_currency(workspace_id: int) -> str:
    return str(get_workspace_settings(workspace_id).get("base_currency") or "SEK").upper()


def convert_to_base(workspace_id: int, amount: float, currency: str) -> float:
    rate = get_fx_rate(workspace_id, currency)
    if rate is None:
        base = base_currency(workspace_id)
        raise HTTPException(
            status_code=409,
            detail=f"Missing FX rate for {currency.upper()} → {base}. Add it under workspace settings before aggregating this currency.",
        )
    return float(amount) * rate


def maybe_convert_to_base(workspace_id: int, amount: float, currency: str) -> tuple[float | None, str]:
    base = base_currency(workspace_id)
    rate = get_fx_rate(workspace_id, currency)
    if rate is None:
        return None, base
    return float(amount) * rate, base
