from fastapi.testclient import TestClient

from app.main import app


def test_marketing_root_uses_one_shot_runtime_instead_of_mutation_loop_helper():
    with TestClient(app) as client:
        page = client.get('/')
        safe_runtime = client.get('/static/landing-runtime-safe.js')

    assert page.status_code == 200
    assert safe_runtime.status_code == 200
    assert '/static/landing-runtime-safe.js?build=' in page.text
    assert '/static/landing-ux.js?build=' not in page.text

    script = safe_runtime.text
    assert 'MutationObserver' not in script
    assert 'DOMContentLoaded' in script
    assert 'dataset.vexmeraRuntimeStable' in script


def test_marketing_runtime_keeps_sound_default_without_repeated_dom_observation():
    with TestClient(app) as client:
        script = client.get('/static/landing-runtime-safe.js').text

    assert "localStorage.getItem('vexmera-sound') === null" in script
    assert "localStorage.setItem('vexmera-sound', 'on')" in script
    assert 'setOnce' in script
