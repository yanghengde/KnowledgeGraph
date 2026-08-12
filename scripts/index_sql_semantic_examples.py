#!/usr/bin/env python3
"""Build the dedicated vector collection for SQL metric examples."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.qa.semantic.example_index import (  # noqa: E402
    COLLECTION_NAME,
    load_semantic_examples,
    rebuild_semantic_example_index,
)


def main() -> int:
    expected = len(load_semantic_examples())
    indexed = rebuild_semantic_example_index()
    print(json.dumps(
        {
            "collection": COLLECTION_NAME,
            "expected": expected,
            "indexed": indexed,
        },
        ensure_ascii=False,
    ))
    return 0 if indexed == expected else 1


if __name__ == "__main__":
    raise SystemExit(main())
