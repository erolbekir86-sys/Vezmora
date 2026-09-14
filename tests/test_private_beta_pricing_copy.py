from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RUNTIME = (ROOT / "static" / "landing-runtime-safe.js").read_text(encoding="utf-8")


def test_private_beta_pricing_note_does_not_advertise_available_annual_discount():
    assert "alignPrivateBetaPricingCopy" in RUNTIME
    assert "Priser exkl. moms. Årsbetalning öppnas efter privat beta." in RUNTIME
    assert "Prices exclude VAT. Annual billing opens after the private beta." in RUNTIME
    assert "alignPrivateBetaPricingCopy();" in RUNTIME
