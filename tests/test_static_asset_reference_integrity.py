from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
STATIC_REF_RE = re.compile(
    r"/static/([A-Za-z0-9._/-]+\.(?:js|css|jpe?g|png|svg|webp|woff2?))",
    re.IGNORECASE,
)


def test_all_local_static_references_exist_and_are_non_empty():
    """Protect runtime-loaded frontend assets from missing-file regressions.

    Vexmera loads several assets dynamically from JavaScript/CSS, so checking only
    references present in the server-rendered HTML is not enough. This scans every
    shipped text frontend asset and verifies that each local /static/... reference
    resolves to a real, non-empty file in the repository.
    """

    references: dict[str, set[Path]] = {}
    for source in STATIC.rglob("*"):
        if source.suffix.lower() not in {".html", ".js", ".css"}:
            continue
        text = source.read_text(encoding="utf-8")
        for relative in STATIC_REF_RE.findall(text):
            references.setdefault(relative, set()).add(source.relative_to(ROOT))

    assert references, "expected at least one local /static/ asset reference"

    missing: list[str] = []
    empty: list[str] = []
    for relative, sources in sorted(references.items()):
        target = STATIC / relative
        source_list = ", ".join(str(path) for path in sorted(sources))
        if not target.is_file():
            missing.append(f"/static/{relative} referenced by {source_list}")
        elif target.stat().st_size == 0:
            empty.append(f"/static/{relative} referenced by {source_list}")

    assert not missing, "missing local static assets:\n" + "\n".join(missing)
    assert not empty, "empty local static assets:\n" + "\n".join(empty)
