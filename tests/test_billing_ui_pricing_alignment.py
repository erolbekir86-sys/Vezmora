from pathlib import Path

from app.pricing import PLANS


ROOT = Path(__file__).resolve().parents[1]


def _format_sek(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def test_self_service_billing_ui_matches_canonical_pricing() -> None:
    """Keep the client-side billing labels tied to the backend pricing source."""
    script = (ROOT / "static" / "self-service-alignment.js").read_text(encoding="utf-8")

    positions: list[int] = []
    for key in ("start", "growth", "pro"):
        plan = PLANS[key]
        label = str(plan["label"])
        price = f"{_format_sek(int(plan['monthly_price_sek']))} kr"
        expected = (
            f"{{key: '{key}', label: '{label}', price: '{price}', "
            f"button: 'Välj {label}'}}"
        )
        assert expected in script
        positions.append(script.index(expected))

    assert positions == sorted(positions)
    assert "{key: 'starter'" not in script
    assert "{key: 'scale'" not in script
