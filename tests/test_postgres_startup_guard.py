from __future__ import annotations

from pathlib import Path


DEPLOYMENT_SOURCE = Path(__file__).resolve().parents[1] / "main.py"


def test_postgres_startup_override_is_installed_after_app_main_import():
    """Guard the Vercel/Postgres bootstrap ordering that previously regressed.

    app.postgres_compat imports the app package, which can load app.main before
    deployment main.py replaces store.init_db. FastAPI's lifespan resolves the
    module-level app.main.init_db name at runtime, so the deployment wrapper must
    replace that name after app.main is imported whenever Postgres is active.
    """

    source = DEPLOYMENT_SOURCE.read_text(encoding="utf-8")

    store_override = "_store.init_db = _verify_database"
    app_import = "from app.main import app, main"
    app_override = "_app_main.init_db = _verify_database"
    guarded_app_override = "if postgres_url:\n    _app_main.init_db = _verify_database"

    assert store_override in source
    assert app_import in source
    assert app_override in source
    assert guarded_app_override in source

    # The store override is installed before importing app.main, and the
    # app.main module-level name is repaired immediately afterwards. This
    # ordering prevents the lifespan from calling SQLite schema DDL on Postgres.
    assert source.index(store_override) < source.index(app_import) < source.index(app_override)


def test_postgres_startup_uses_connectivity_check_not_schema_bootstrap():
    source = DEPLOYMENT_SOURCE.read_text(encoding="utf-8")

    verify_start = source.index("def _verify_database() -> None:")
    verify_end = source.index("_store.init_db = _verify_database", verify_start)
    verify_body = source[verify_start:verify_end]

    assert 'con.execute("SELECT 1")' in verify_body
    assert "CREATE TABLE" not in verify_body.upper()
    assert "DROP TABLE" not in verify_body.upper()
