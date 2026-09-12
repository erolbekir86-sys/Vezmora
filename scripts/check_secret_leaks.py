from __future__ import annotations

import re
import subprocess
from pathlib import Path


MAX_FILE_BYTES = 1_000_000

# High-confidence credential formats only. The goal is to catch accidental real
# credentials without blocking ordinary documentation, IDs, URLs, or examples.
_SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("OpenAI API key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b")),
    ("Stripe secret key", re.compile(r"\bsk_(?:live|test)_[A-Za-z0-9]{20,}\b")),
    ("Stripe webhook secret", re.compile(r"\bwhsec_[A-Za-z0-9]{20,}\b")),
    ("GitHub personal access token", re.compile(r"\bgh[opusr]_[A-Za-z0-9]{30,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{20,}\b")),
    ("Private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
)


def tracked_files(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return [root / item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def scan_text(text: str) -> list[str]:
    findings: list[str] = []
    for label, pattern in _SECRET_PATTERNS:
        if pattern.search(text):
            findings.append(label)
    return findings


def scan_file(path: Path) -> list[str]:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return []
        raw = path.read_bytes()
    except (OSError, FileNotFoundError):
        return []
    if b"\0" in raw:
        return []
    return scan_text(raw.decode("utf-8", errors="ignore"))


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    failures: list[tuple[str, str]] = []
    for path in tracked_files(root):
        for label in scan_file(path):
            failures.append((str(path.relative_to(root)), label))

    if failures:
        print("Potential committed secrets detected:")
        for path, label in failures:
            print(f"- {path}: {label}")
        print("Remove/rotate the credential before merging. Values are intentionally not printed.")
        return 1

    print("Secret scan passed: no high-confidence credential patterns found in tracked text files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
