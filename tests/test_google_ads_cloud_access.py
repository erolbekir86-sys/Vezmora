"""Exercise the Google connection against fake HTTP, never live ad mutations."""
import asyncio
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
from fastapi import HTTPException

from app import connectors, google_ads_diagnostics as diagnostics
from app import google_oauth_transport_safety as oauth
from app import google_read_reliability as reliability


def install_transport(monkeypatch, responses):
    calls = []
    pending = list(responses)

    def respond(request):
        calls.append(request)
        assert pending, 'Unexpected extra request'
        return pending.pop(0)

    real_client = httpx.AsyncClient
    monkeypatch.setattr(httpx, 'AsyncClient', lambda **kw: real_client(transport=httpx.MockTransport(respond), **kw))
    return calls


@pytest.mark.parametrize('legacy_token', [None, 'obsolete-token'])
def test_read_sync_works_without_developer_token_and_never_sends_it(monkeypatch, legacy_token):
    if legacy_token:
        monkeypatch.setenv('GOOGLE_ADS_DEVELOPER_TOKEN', legacy_token)
    else:
        monkeypatch.delenv('GOOGLE_ADS_DEVELOPER_TOKEN', raising=False)
    monkeypatch.setenv('GOOGLE_ADS_API_VERSION', 'v25')
    monkeypatch.setenv('GOOGLE_ADS_LOGIN_CUSTOMER_ID', '944-502-2492')
    connector = {'status': 'connected', 'metadata': {'ads_customer_id': '638-343-6270'}}
    monkeypatch.setattr(reliability, 'get_connector', lambda *a, **k: connector)
    monkeypatch.setattr(reliability, 'get_workspace_settings', lambda *a: {'base_currency': 'SEK'})
    monkeypatch.setattr(reliability, 'get_fx_rate', lambda *a: 1)
    async def refresh(*a):
        return 'test-access', {}
    monkeypatch.setattr(reliability, 'refresh_google_access_token_reliable', refresh)
    monkeypatch.setattr(reliability, 'update_connector_metadata', lambda *a: None)
    monkeypatch.setattr(connectors, 'update_connector_metadata', lambda *a: None)
    monkeypatch.setattr(reliability, 'add_notification', lambda *a: None)
    campaigns, kpis = [], []
    monkeypatch.setattr(reliability, 'upsert_campaign_metric', lambda wid, data: campaigns.append(data))
    monkeypatch.setattr(reliability, 'upsert_kpi', lambda wid, data: kpis.append(data))
    row = {'segments': {'date': '2026-09-12'}, 'customer': {'currencyCode': 'SEK'}, 'campaign': {'id': '1', 'name': 'Test'}, 'metrics': {'costMicros': '12000000', 'clicks': '3', 'impressions': '100', 'conversions': 1}}
    calls = install_transport(monkeypatch, [httpx.Response(200, json=[{'results': [row]}])])
    result = asyncio.run(connectors.sync_google(7))
    assert result['campaign_rows'] == result['ads_rows'] == 1
    assert len(campaigns) == len(kpis) == 1
    assert campaigns[0]['spend'] == 12
    assert len(calls) == 1
    assert calls[0].url.path == '/v25/customers/6383436270/googleAds:searchStream'
    assert calls[0].headers['login-customer-id'] == '9445022492'
    assert 'developer-token' not in calls[0].headers


def test_original_stream_error_is_reported_without_second_probe(monkeypatch):
    monkeypatch.setattr(reliability, 'get_connector', lambda *a, **k: {'status': 'connected', 'metadata': {'ads_customer_id': '6383436270'}})
    monkeypatch.setattr(reliability, 'get_workspace_settings', lambda *a: {})
    async def refresh(*a):
        return 'test-access', {}
    monkeypatch.setattr(reliability, 'refresh_google_access_token_reliable', refresh)
    monkeypatch.setattr(reliability, 'update_connector_metadata', lambda *a: None)
    monkeypatch.setattr(connectors, 'update_connector_metadata', lambda *a: None)
    monkeypatch.setattr(reliability, 'add_notification', lambda *a: None)
    monkeypatch.setattr(reliability, 'upsert_campaign_metric', lambda *a: pytest.fail('Must not save failed data'))
    body = [{'error': {'status': 'PERMISSION_DENIED', 'details': [{'errors': [{'errorCode': {'authorizationError': 'CLOUD_PROJECT_NOT_APPROVED_FOR_PRODUCTION'}}]}]}}]
    calls = install_transport(monkeypatch, [httpx.Response(403, json=body, headers={'request-id': 'req-actual'})])
    result = asyncio.run(connectors.sync_google(7))
    warning = ' '.join(result['warnings'])
    assert 'CLOUD_PROJECT_NOT_APPROVED_FOR_PRODUCTION' in warning
    assert 'req-actual' in warning
    assert 'Explorer' in warning
    assert 'No campaign data' not in warning
    assert len(calls) == 1


def configure_callback(monkeypatch):
    monkeypatch.setenv('GOOGLE_CLIENT_ID', 'test-client.apps.googleusercontent.com')
    monkeypatch.setenv('GOOGLE_CLIENT_SECRET', 'test-secret')
    monkeypatch.setenv('GOOGLE_REDIRECT_URI', 'https://vexmera.com/api/connectors/google/callback')
    monkeypatch.setattr(connectors, 'consume_oauth_state', lambda *a: {'workspace_id': 7})
    monkeypatch.setattr(connectors, 'get_connector', lambda *a, **k: {'metadata': {'ads_customer_id': '6383436270', 'analytics_property_id': '123', 'last_sync': {'old': True}}})
    monkeypatch.setattr(connectors, 'encrypt_json', lambda token: 'encrypted')


def test_oauth_start_and_exchange_match_and_preserve_source_settings(monkeypatch):
    configure_callback(monkeypatch)
    monkeypatch.setattr(connectors, 'save_oauth_state', lambda *a: None)
    saved = []
    monkeypatch.setattr(connectors, 'save_connector', lambda **k: saved.append(k))
    url = connectors.google_authorization_url(7, 1)
    params = parse_qs(urlsplit(url).query)
    calls = install_transport(monkeypatch, [httpx.Response(200, json={'access_token': 'new', 'refresh_token': 'new-refresh', 'scope': 'ads'})])
    asyncio.run(oauth.google_callback_safe('code', params['state'][0]))
    exchange = parse_qs(calls[0].content.decode())
    assert params['client_id'] == exchange['client_id']
    assert params['redirect_uri'] == exchange['redirect_uri'] == ['https://vexmera.com/api/connectors/google/callback']
    assert params['access_type'] == ['offline']
    assert params['prompt'] == ['consent']
    assert saved[0]['metadata']['ads_customer_id'] == '6383436270'
    assert saved[0]['metadata']['analytics_property_id'] == '123'
    assert 'last_sync' not in saved[0]['metadata']


@pytest.mark.parametrize('error,status', [('invalid_client', 503), ('invalid_grant', 409)])
def test_oauth_errors_are_actionable_without_returning_secrets(monkeypatch, error, status):
    configure_callback(monkeypatch)
    monkeypatch.setattr(connectors, 'save_connector', lambda **k: pytest.fail('Must not replace connection'))
    install_transport(monkeypatch, [httpx.Response(400, json={'error': error, 'error_description': 'test-secret'})])
    with pytest.raises(HTTPException) as exc:
        asyncio.run(oauth.google_callback_safe('code', 'state'))
    assert exc.value.status_code == status
    assert 'test-secret' not in exc.value.detail


def test_missing_offline_token_does_not_overwrite_existing_connection(monkeypatch):
    configure_callback(monkeypatch)
    monkeypatch.setattr(connectors, 'save_connector', lambda **k: pytest.fail('Must not replace connection'))
    install_transport(monkeypatch, [httpx.Response(200, json={'access_token': 'new'})])
    with pytest.raises(HTTPException, match='offline access'):
        asyncio.run(oauth.google_callback_safe('code', 'state'))


@pytest.mark.parametrize('error,status', [('invalid_grant', 409), ('invalid_client', 503)])
def test_refresh_rejection_does_not_fall_back_to_stale_access_token(monkeypatch, error, status):
    configure_callback(monkeypatch)
    monkeypatch.setattr(connectors, 'decrypt_json', lambda *a: {'access_token': 'old', 'refresh_token': 'revoked'})
    calls = install_transport(monkeypatch, [httpx.Response(400, json={'error': error})])
    with pytest.raises(HTTPException) as exc:
        asyncio.run(reliability.refresh_google_access_token_reliable(7, {'secret_blob': 'encrypted'}))
    assert exc.value.status_code == status
    assert len(calls) == 1
