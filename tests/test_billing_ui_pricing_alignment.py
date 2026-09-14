from pathlib import Path
from html.parser import HTMLParser

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


def test_static_billing_matches_canonical_prices_before_javascript() -> None:
    html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    for key, plan in PLANS.items():
        price = f"{_format_sek(int(plan['monthly_price_sek']))} kr"
        assert f"<span>{plan['label']}</span><strong>{price}</strong>" in html
        assert f'data-plan="{key}"' in html
    assert 'data-plan="starter"' not in html
    assert 'data-plan="scale"' not in html


def test_static_checkout_stays_disabled_until_readiness_is_verified() -> None:
    class Buttons(HTMLParser):
        def __init__(self):
            super().__init__()
            self.plans = []

        def handle_starttag(self, tag, attrs):
            attributes = dict(attrs)
            if tag == "button" and "data-plan" in attributes:
                self.plans.append(attributes)

    parser = Buttons()
    parser.feed((ROOT / "static" / "index.html").read_text(encoding="utf-8"))
    assert len(parser.plans) == len(PLANS)
    assert all("disabled" in button for button in parser.plans)
