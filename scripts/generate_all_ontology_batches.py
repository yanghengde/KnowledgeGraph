#!/usr/bin/env python3
"""Regenerate every reviewed semiconductor ontology batch in dependency order."""

from pathlib import Path

from generate_ontology_batch import DEFAULT_FIELDS, DEFAULT_ONTOLOGY_DIR, DEFAULT_TABLES, generate
from maintenance.apply_sql_learning_scope import apply_scope


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BATCH_DIR = PROJECT_ROOT / "src" / "ontology" / "batches"


def main() -> int:
    configs = sorted(BATCH_DIR.glob("[0-9][0-9]_*.json"))
    for config in configs:
        ontology_path, modeling_path = generate(
            config,
            DEFAULT_TABLES,
            DEFAULT_FIELDS,
            DEFAULT_ONTOLOGY_DIR,
        )
        print(f"{config.name}: {ontology_path.name}, {modeling_path.name}")
    scope_result = apply_scope(DEFAULT_ONTOLOGY_DIR, write=True)
    print(f"generated_batches={len(configs)}")
    print(
        "sql_learning_scope="
        f"{scope_result['classes_removed']} classes, "
        f"{scope_result['relationships_removed']} relationships removed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
