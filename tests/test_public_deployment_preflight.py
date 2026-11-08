from scripts import public_deployment_preflight as preflight

SHA = 'a' * 40


def fixture(monkeypatch, overrides=None):
    seen = []
    overrides = overrides or {}
    monkeypatch.setattr(preflight, 'build_public_runtime_preflight', lambda base, expected_revision: {'ok': expected_revision == SHA})
    def get(url):
        seen.append(url)
        path = url.removeprefix('https://example.test')
        if path in overrides:
            return overrides[path]
        if path in ('/', '/app'):
            return 200, '<script src="/static/loader.js"></script>'
        if path == '/static/loader.js':
            return 200, 'load("/static/loaded.css");'
        if path == '/static/loaded.css':
            return 200, 'body{color:black}'
        return preflight._ROUTES[path], ''
    monkeypatch.setattr(preflight, '_get', get)
    return seen


def test_deployed_route_and_dynamic_asset_graph_pass(monkeypatch):
    seen = fixture(monkeypatch)
    result = preflight.build_public_deployment_preflight('https://example.test', SHA)
    assert result['ok'] is True
    assert result['scope'] == 'public_get_only_deployment_checks'
    assert len(result['checks']) == 10
    assert len(result['assets']) == 2
    assert len(seen) == len(set(seen))
    assert 'authenticated browser' in result['note']


def test_refuses_ambiguous_origin_before_any_network(monkeypatch):
    seen = fixture(monkeypatch)
    result = preflight.build_public_deployment_preflight('https://user:secret@example.test/path', SHA)
    assert result['blockers'] == ['invalid_base_url']
    assert seen == []


def test_revision_gate_stops_public_tests_on_wrong_build(monkeypatch):
    seen = fixture(monkeypatch)
    monkeypatch.setattr(preflight, 'build_public_runtime_preflight', lambda *args, **kwargs: {'ok': False})
    result = preflight.build_public_deployment_preflight('https://example.test', SHA)
    assert result['blockers'] == ['runtime_gate_failed']
    assert seen == []


def test_refuses_short_revision(monkeypatch):
    seen = fixture(monkeypatch)
    assert preflight.build_public_deployment_preflight('https://example.test', 'abc123')['ok'] is False
    assert seen == []


def test_unauthenticated_workspace_exposure_fails(monkeypatch):
    fixture(monkeypatch, {'/api/workspaces': (200, '[{"name":"private"}]')})
    result = preflight.build_public_deployment_preflight('https://example.test', SHA)
    assert result['ok'] is False
    assert 'route_failed:/api/workspaces' in result['blockers']
    assert 'private' not in str(result)


def test_missing_loader_asset_fails(monkeypatch):
    fixture(monkeypatch, {'/static/loaded.css': (404, '')})
    result = preflight.build_public_deployment_preflight('https://example.test', SHA)
    assert result['ok'] is False
    assert 'asset_failed:/static/loaded.css' in result['blockers']


def test_asset_traversal_is_never_requested(monkeypatch):
    seen = fixture(monkeypatch, {'/static/loader.js': (200, 'load("/static/../private.js");')})
    result = preflight.build_public_deployment_preflight('https://example.test', SHA)
    assert result['ok'] is True
    assert not any('/../' in url for url in seen)


def test_asset_graph_is_bounded(monkeypatch):
    fixture(monkeypatch)
    monkeypatch.setattr(preflight, '_MAX_ASSETS', 1)
    result = preflight.build_public_deployment_preflight('https://example.test', SHA)
    assert result['ok'] is False
    assert 'asset_limit_exceeded' in result['blockers']
