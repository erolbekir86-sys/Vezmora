from pathlib import Path

from scripts.check_secret_leaks import scan_file, scan_text


def _joined(*parts: str) -> str:
    return "".join(parts)


def test_detects_high_confidence_credentials_without_echoing_values(tmp_path: Path):
    samples = {
        "OpenAI API key": _joined("sk-", "proj-", "A" * 32),
        "Stripe secret key": _joined("sk_", "live_", "B" * 32),
        "Stripe webhook secret": _joined("whsec_", "C" * 32),
        "GitHub personal access token": _joined("ghp_", "D" * 36),
        "Google API key": _joined("AIza", "E" * 35),
        "Slack token": _joined("xoxb-", "1234567890-", "F" * 24),
        "Private key": _joined("-----BEGIN ", "PRIVATE KEY-----"),
    }

    for expected, value in samples.items():
        findings = scan_text(f"credential={value}")
        assert expected in findings
        assert value not in findings

    path = tmp_path / "secret.txt"
    path.write_text(samples["Stripe webhook secret"], encoding="utf-8")
    assert scan_file(path) == ["Stripe webhook secret"]


def test_allows_placeholders_and_public_identifiers():
    benign = "\n".join(
        [
            "OPENAI_API_KEY=",
            "STRIPE_SECRET_KEY=sk_test_REPLACE_ME",
            "STRIPE_WEBHOOK_SECRET=whsec_example",
            "GOOGLE_CLIENT_ID=123.apps.googleusercontent.com",
            "STRIPE_PRICE_PRO=price_123456789",
            "VEZMORA_SECRET_KEY=change-me-locally",
        ]
    )
    assert scan_text(benign) == []


def test_skips_binary_and_oversized_files(tmp_path: Path, monkeypatch):
    binary = tmp_path / "binary.bin"
    binary.write_bytes(b"\x00" + _joined("sk_", "live_", "G" * 32).encode())
    assert scan_file(binary) == []

    oversized = tmp_path / "large.txt"
    oversized.write_text(_joined("sk_", "live_", "H" * 32), encoding="utf-8")
    monkeypatch.setattr("scripts.check_secret_leaks.MAX_FILE_BYTES", 1)
    assert scan_file(oversized) == []
