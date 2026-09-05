from __future__ import annotations

import json

from app.stripe_catalog import verify_configured_prices


def main() -> int:
    result = verify_configured_prices()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
