from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_product_shell_loads_billing_return_feedback_after_toast_layer() -> None:
    with TestClient(app) as client:
        response = client.get('/app')
        script = client.get('/static/billing-return-ui.js')

    assert response.status_code == 200
    assert script.status_code == 200
    html = response.text
    polish = html.index('/static/app-polish-safe.js?build=')
    billing = html.index('/static/billing-return-ui.js?build=')
    assert polish < billing


def test_billing_return_ui_scrubs_checkout_markers_and_does_not_overclaim_activation() -> None:
    with TestClient(app) as client:
        source = client.get('/static/billing-return-ui.js').text

    assert "result !== 'success' && result !== 'cancelled'" in source
    assert "params.delete('billing')" in source
    assert "params.delete('session_id')" in source
    assert source.index("params.delete('session_id')") < source.index('window.vexmeraToast(message)')
    assert 'verifierar abonnemangsstatus via Stripe' in source
    assert 'Inga abonnemangsändringar genomfördes' in source
    assert 'abonnemanget är aktivt' not in source.lower()
