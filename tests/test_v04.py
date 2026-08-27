from fastapi.testclient import TestClient

from app import store
from app.main import app
from app.monitor import normalize_page


def register(client: TestClient):
    result = client.post('/api/auth/register', json={
        'email': 'v04@example.com',
        'password': 'verysecure123',
        'workspace_name': 'Vexmera 04',
    })
    assert result.status_code == 200
    return result.json()['workspace_id']


def test_approval_notifications_and_brief_settings(tmp_path, monkeypatch):
    monkeypatch.setattr(store, 'DB_PATH', tmp_path / 'v04.db')
    store.init_db()
    with TestClient(app) as client:
        workspace_id = register(client)

        created = client.post(f'/api/approvals?workspace_id={workspace_id}', json={
            'action_type': 'campaign_draft',
            'title': 'Approve autumn launch',
            'description': 'Review this draft before any publishing.',
            'provider': 'meta',
            'risk_level': 'high',
            'payload': {'budget_sek': 5000},
        })
        assert created.status_code == 200
        approval_id = created.json()['id']

        pending = client.get(f'/api/approvals?workspace_id={workspace_id}&status=pending').json()
        assert pending[0]['id'] == approval_id
        assert pending[0]['status'] == 'pending'

        decision = client.post(f'/api/approvals/{approval_id}/approve?workspace_id={workspace_id}', json={'note': 'Looks good'})
        assert decision.status_code == 200
        approved = client.get(f'/api/approvals?workspace_id={workspace_id}&status=approved').json()
        assert approved[0]['review_note'] == 'Looks good'

        notifications = client.get(f'/api/notifications?workspace_id={workspace_id}').json()
        assert len(notifications) >= 2

        settings = client.put(f'/api/briefs/settings?workspace_id={workspace_id}', json={
            'enabled': True,
            'hour': 8,
            'timezone': 'Europe/Stockholm',
        })
        assert settings.status_code == 200
        loaded = client.get(f'/api/briefs/settings?workspace_id={workspace_id}').json()
        assert loaded['enabled'] == 1
        assert loaded['hour'] == 8


def test_page_normalizer_is_stable_for_scripts():
    a = '<html><head><title>Acme</title><script>var x=1</script></head><body><h1>Sale</h1><p>20% off</p></body></html>'
    b = '<html><head><title>Acme</title><script>var x=999</script></head><body><h1>Sale</h1><p>20% off</p></body></html>'
    title_a, excerpt_a, hash_a = normalize_page(a)
    title_b, excerpt_b, hash_b = normalize_page(b)
    assert title_a == title_b == 'Acme'
    assert excerpt_a == excerpt_b
    assert hash_a == hash_b
