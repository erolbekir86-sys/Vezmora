from __future__ import annotations

import re
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _project_version() -> str:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def test_runtime_and_public_health_match_package_release_version() -> None:
    """Prevent a release from advertising different versions across runtime surfaces."""

    expected = _project_version()
    main_source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
    public_health_source = (ROOT / "app" / "public_health.py").read_text(encoding="utf-8")

    api_version = re.search(r'FastAPI\([^\n]*version="([^"]+)"', main_source)
    health_version = re.search(r'"version":\s*"([^"]+)"', public_health_source)

    assert api_version is not None, "FastAPI runtime version declaration is missing"
    assert health_version is not None, "Public health version declaration is missing"
    assert api_version.group(1) == expected
    assert health_version.group(1) == expected
