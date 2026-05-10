from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate minimal Nexus agent plan + provenance artifacts for CI."
    )
    parser.add_argument("--plan-dir", required=True)
    parser.add_argument("--provenance-dir", required=True)
    args = parser.parse_args()

    plan_dir = Path(args.plan_dir)
    prov_dir = Path(args.provenance_dir)
    plan_dir.mkdir(parents=True, exist_ok=True)
    prov_dir.mkdir(parents=True, exist_ok=True)

    (plan_dir / "plan.json").write_text(
        json.dumps(
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "plan": [
                    "Clarify requested Web3 interfaces/pages and required components.",
                    "Implement UI and wire to wallet/provider + contracts.",
                    "Add tests/lint and rerun CI.",
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    (prov_dir / "provenance.json").write_text(
        json.dumps(
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "source": "github-actions",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
