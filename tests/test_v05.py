from datetime import date, timedelta

from fastapi.testclient import TestClient

from app import store
from app.analytics import detect_anomalies
from app.main import app


def register(client: TestClient, email: str = "owner05@example.com") -> int:
    res = client.post('/api/auth/register', json={
        'email': email,
        'password': 'verysecure123',
        'workspace_name': 'Vexmera 05',
    })
    assert res.status_code == 200
    return res.json()['workspace_id']


def test_multicurrency_campaigns_jobs_and_execution_gate(tmp_path, monkeypatch):
    monkeypatch.setattr(store, 'DB_PATH', tmp_path / 'v05.db')
    store.init_db()
    with TestClient(app) as client:
        workspace_id = register(client)
        assert client.put(f'/api/workspace/settings?workspace_id={workspace_id}', json={'base_currency': 'EUR'}).status_code == 200
        assert client.put(f'/api/fx-rates?workspace_id={workspace_id}', json={'quote_currency': 'USD', 'rate_to_base': 0.9}).status_code == 200

        kpi = client.post(f'/api/kpis?workspace_id={workspace_id}', json={
            'date': '2026-08-24', 'currency': 'USD', 'impressions': 1000, 'clicks': 50,
            'leads': 5, 'conversions': 2, 'spend_sek': 100, 'revenue_sek': 500, 'source': 'manual',
        })
        assert kpi.status_code == 200
        dash = client.get(f'/api/dashboard?workspace_id={workspace_id}').json()
        assert dash['base_currency'] == 'EUR'
        assert dash['spend_sek'] == 90
        assert dash['revenue_sek'] == 450

        store.upsert_campaign_metric(workspace_id, {
            'provider': 'google_ads', 'external_campaign_id': '123', 'campaign_name': 'Search EU',
            'date': '2026-08-24', 'impressions': 1000, 'clicks': 100, 'conversions': 10,
            'spend': 100, 'revenue': 400, 'currency': 'EUR',
        })
        campaigns = client.get(f'/api/campaigns?workspace_id={workspace_id}&days=30').json()
        assert campaigns[0]['campaign_name'] == 'Search EU'
        assert campaigns[0]['roas'] == 4

        job = client.post(f'/api/jobs?workspace_id={workspace_id}', json={'kind': 'detect_anomalies', 'payload': {}})
        assert job.status_code == 200
        jobs = client.get(f'/api/jobs?workspace_id={workspace_id}').json()
        assert jobs[0]['status'] == 'queued'

        approval = client.post(f'/api/approvals?workspace_id={workspace_id}', json={
            'action_type': 'google.pause_campaign', 'title': 'Pause campaign',
            'description': 'Pause after review', 'provider': 'google', 'risk_level': 'high',
            'payload': {'campaign_id': '123'},
        }).json()['id']
        assert client.post(f'/api/approvals/{approval}/approve?workspace_id={workspace_id}', json={'note': 'approved'}).status_code == 200
        preview = client.get(f'/api/executions/{approval}/preview?workspace_id={workspace_id}')
        assert preview.status_code == 200
        assert preview.json()['changes']['status'] == 'PAUSED'
        monkeypatch.delenv('VEZMORA_EXECUTION_ENABLED', raising=False)
        execute = client.post(f'/api/executions/{approval}/run?workspace_id={workspace_id}', json={'confirm': True})
        assert execute.status_code == 409


def test_team_invite_and_roles(tmp_path, monkeypatch):
    monkeypatch.setattr(store, 'DB_PATH', tmp_path / 'team05.db')
    store.init_db()
    with TestClient(app) as client:
        workspace_id = register(client, 'owner-team@example.com')
        invite = client.post(f'/api/team/invites?workspace_id={workspace_id}', json={'email': 'viewer@example.com', 'role': 'viewer'})
        assert invite.status_code == 200
        token = invite.json()['invite_token']
        client.post('/api/auth/logout')
        register(client, 'viewer@example.com')
        join = client.post('/api/team/join', json={'token': token})
        assert join.status_code == 200
        assert join.json()['role'] == 'viewer'
        forbidden = client.put(f'/api/workspace/settings?workspace_id={workspace_id}', json={'base_currency': 'USD'})
        assert forbidden.status_code == 403


def test_anomaly_detector(tmp_path, monkeypatch):
    monkeypatch.setattr(store, 'DB_PATH', tmp_path / 'anom05.db')
    store.init_db()
    uid, workspace_id = store.create_user('anom@example.com', 'aa', 'bb', 'Anomaly Lab')
    anchor = date(2026, 8, 24)
    for i in range(7, 14):
        d = anchor - timedelta(days=i)
        store.add_kpi(workspace_id, {'date': d.isoformat(), 'impressions': 1000, 'clicks': 100, 'leads': 10, 'conversions': 10, 'spend_sek': 100, 'revenue_sek': 500, 'source': f'prev-{i}', 'currency': 'SEK'})
    for i in range(0, 7):
        d = anchor - timedelta(days=i)
        store.add_kpi(workspace_id, {'date': d.isoformat(), 'impressions': 1000, 'clicks': 50, 'leads': 5, 'conversions': 3, 'spend_sek': 140, 'revenue_sek': 140, 'source': f'cur-{i}', 'currency': 'SEK'})
    findings = detect_anomalies(workspace_id, anchor=anchor)
    codes = {f['metadata']['code'] for f in findings}
    assert 'roas_drop' in codes
    assert 'ctr_drop' in codes
    assert 'conversion_drop' in codes
