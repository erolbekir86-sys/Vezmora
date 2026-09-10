from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_deployment_entrypoint_does_not_define_second_security_middleware() -> None:
    entrypoint = (ROOT / "main.py").read_text(encoding="utf-8")

    assert "production_security_headers" not in entrypoint
    assert "def _https_runtime" not in entrypoint
    assert "app.security_headers" in entrypoint


def test_package_installs_canonical_security_middleware() -> None:
    package_init = (ROOT / "app" / "__init__.py").read_text(encoding="utf-8")

    assert "from .security_headers import install_security_headers" in package_init
    assert "_install_security_headers(_app)" in package_init
