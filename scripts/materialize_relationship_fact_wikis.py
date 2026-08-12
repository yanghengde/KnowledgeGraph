#!/usr/bin/env python3
"""Persist one physical-fact Wiki for every current ontology relationship."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ontology.wiki_manager import materialize_factual_relationship_wikis


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--product-line", default="general")
    parser.add_argument(
        "--no-upgrade-existing",
        action="store_true",
        help="Do not insert SQL into existing authored Wikis",
    )
    args = parser.parse_args()
    stats = materialize_factual_relationship_wikis(
        product_line=args.product_line,
        upgrade_existing=not args.no_upgrade_existing,
    )
    print(json.dumps(stats, ensure_ascii=False))
    return 1 if stats["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
