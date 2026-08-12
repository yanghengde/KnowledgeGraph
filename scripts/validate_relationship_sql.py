#!/usr/bin/env python3
"""Validate SQL examples for every canonical ontology relationship.

The validator is intentionally read-only.  It resolves each relationship
against ``docs/Database_Fields.csv`` and renders both supported SQL dialects.
It exits with a non-zero status when any relationship cannot produce a
deterministic physical JOIN example.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ontology.wiki_manager import (  # noqa: E402
    build_relationship_sql_section,
    collect_all_relationships,
    resolve_relationship_join,
)


SQL_DIALECTS = ("oracle", "sqlserver")


def audit_relationship_sql() -> dict:
    relationships = collect_all_relationships()
    failures: list[dict] = []
    resolution_counts: Counter[str] = Counter()
    direction_counts: Counter[str] = Counter()
    dialect_counts: Counter[str] = Counter()

    for relationship in relationships:
        source = relationship["fromClass"]
        relation = relationship["relationName"]
        target = relationship["toClass"]
        description = relationship.get("description", "")
        join = resolve_relationship_join(source, target, description)

        if not join.get("resolved"):
            failures.append(
                {
                    "source": source,
                    "relationship": relation,
                    "target": target,
                    "description": description,
                    "sourceFile": relationship.get("source_file", ""),
                    "reason": join.get("reason", "unresolved_physical_join"),
                    "directCandidates": join.get("directCandidates", 0),
                    "reverseCandidates": join.get("reverseCandidates", 0),
                }
            )
            continue

        resolution_counts[join.get("resolution", "unknown")] += 1
        direction_counts[join.get("direction", "unknown")] += 1

        for dialect in SQL_DIALECTS:
            sql = build_relationship_sql_section(
                source,
                relation,
                target,
                description,
                sql_dialect=dialect,
            )
            if "```sql" not in sql or "LEFT JOIN" not in sql or " ON " not in sql:
                failures.append(
                    {
                        "source": source,
                        "relationship": relation,
                        "target": target,
                        "description": description,
                        "sourceFile": relationship.get("source_file", ""),
                        "dialect": dialect,
                        "reason": "sql_example_not_rendered",
                    }
                )
                continue
            dialect_counts[dialect] += 1

    return {
        "relationships": len(relationships),
        "expectedSqlExamples": len(relationships) * len(SQL_DIALECTS),
        "generatedSqlExamples": sum(dialect_counts.values()),
        "dialects": dict(sorted(dialect_counts.items())),
        "resolutions": dict(sorted(resolution_counts.items())),
        "directions": dict(sorted(direction_counts.items())),
        "failures": failures,
    }


def _print_text_report(report: dict) -> None:
    print("Relationship SQL validation")
    print(f"  Relationships:       {report['relationships']}")
    print(f"  SQL examples:        {report['generatedSqlExamples']}/{report['expectedSqlExamples']}")
    print(f"  Dialects:            {report['dialects']}")
    print(f"  Join resolutions:    {report['resolutions']}")
    print(f"  Join directions:     {report['directions']}")
    print(f"  Failures:            {len(report['failures'])}")
    for failure in report["failures"]:
        print(
            "  - "
            f"{failure['source']} --[{failure['relationship']}]--> {failure['target']}: "
            f"{failure['reason']}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate physical SQL examples for all ontology relationships."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the machine-readable audit result as JSON.",
    )
    args = parser.parse_args()

    report = audit_relationship_sql()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _print_text_report(report)
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
