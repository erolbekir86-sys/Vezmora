from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from app.security_headers import install_security_headers


ROOT = Path(__file__).resolve().parents[1]


def test_deployment_entrypoint_does_not_define_second_security_middleware() -> None:
    entrypoint = (ROOT / "main.py").read_text(encoding="utf-8")

    assert "production_security_headers" not in entrypoint
    assert "def _https_runtime" not in entrypoint
    assert "from app.security_headers import install_security_headers" in entrypoint
    assert "_install_security_headers(app)" in entrypoint


def test_package_installs_canonical_security_middleware() -> None:
    package_init = (ROOT / "app" / "__init__.py").read_text(encoding="utf-8")

    assert "from .security_headers import install_security_headers" in package_init
    assert "_install_security_headers(_app)" in package_init


def test_canonical_security_installer_is_idempotent() -> None:
    app = FastAPI()
    before = len(app.user_middleware)

    install_security_headers(app)
    install_security_headers(app)

    assert len(app.user_middleware) == before + 1
