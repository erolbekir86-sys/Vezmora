from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".py", ".js", ".html", ".md", ".json", ".toml", ".yaml", ".yml", ".txt"}
SKIP_PARTS = {".git", ".venv", "node_modules", "__pycache__"}

# Intentionally target provider formats that should never appear verbatim in
# tracked source/docs. Patterns require realistic lengths to avoid blocking
# obvious placeholder examples.
SECRET_PATTERNS = {
    "OpenAI API key": re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    "Stripe live secret key": re.compile(r"\bsk_live_[A-Za-z0-9]{16,}\b"),
    "Stripe webhook secret": re.compile(r"\bwhsec_[A-Za-z0-9]{16,}\b"),
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
}


def _candidate_files():
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        yield path


def test_repository_contains_no_provider_secret_shaped_literals():
    findings: list[str] = []

    for path in _candidate_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{path.relative_to(ROOT)}: {label}")

    assert findings == [], "Potential committed secrets detected: " + "; ".join(sorted(findings))


def test_environment_files_remain_untracked_by_default():
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".env.*" in gitignore
    assert "!.env.example" in gitignore
