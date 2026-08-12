#!/usr/bin/env python3
"""Audit that all versioned SQL examples are present and immutable in ChromaDB."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.qa.semantic.example_index import (  # noqa: E402
    COLLECTION_NAME,
    get_semantic_example_collection,
    load_semantic_examples,
    resolve_static_sql_example,
)


REPORT = PROJECT_ROOT / "docs" / "sql_semantic_index_report.md"


def main() -> int:
    cases = load_semantic_examples()
    collection = get_semantic_example_collection()
    stored = collection.get(
        include=["documents", "metadatas"],
    )
    stored_by_case = {
        metadata["case_id"]: {
            "document": document,
            "metadata": metadata,
        }
        for document, metadata in zip(
            stored.get("documents") or [],
            stored.get("metadatas") or [],
        )
    }
    indexed = 0
    immutable = 0
    semantic_top1 = 0
    failures = []

    for case in cases:
        saved = stored_by_case.get(case["id"])
        if saved:
            indexed += 1
        else:
            failures.append(f"{case['id']}: 向量条目缺失")
            continue
        metadata = saved["metadata"]
        if (
            saved["document"] == case["question"]
            and metadata.get("metric_id")
            == case["expectedPlan"]["metricId"]
            and metadata.get("golden_sql") == case["goldenSql"]
        ):
            immutable += 1
        else:
            failures.append(f"{case['id']}: 问题、合同或Golden SQL不一致")

        match = resolve_static_sql_example(
            case["question"],
            dialect=case["dialect"],
            metric_id=case["expectedPlan"]["metricId"],
            time_scope=case["expectedPlan"].get("timeScope"),
            time_basis=case["expectedPlan"].get("timeBasis"),
        )
        if (
            match
            and match["case_id"] == case["id"]
            and match["golden_sql"] == case["goldenSql"]
        ):
            semantic_top1 += 1
        else:
            failures.append(f"{case['id']}: 语义检索未返回自身Golden SQL")

    summary = {
        "collection": COLLECTION_NAME,
        "expected": len(cases),
        "collection_count": collection.count(),
        "indexed": indexed,
        "immutable": immutable,
        "semantic_top1": semantic_top1,
        "failures": len(failures),
    }
    lines = [
        "# SQL语义模板向量索引审计",
        "",
        f"- 集合：`{COLLECTION_NAME}`",
        f"- 标准问题：{len(cases)}",
        f"- 集合条目：{collection.count()}",
        f"- 完整入库：{indexed}/{len(cases)}",
        f"- Golden SQL原样一致：{immutable}/{len(cases)}",
        f"- 原问题Top-1命中自身模板：{semantic_top1}/{len(cases)}",
        "",
        "## 失败明细",
        "",
    ]
    lines.extend(f"- {item}" for item in failures)
    if not failures:
        lines.append("_无。_")
    lines += [
        "",
        "向量检索只选择指标合同和固定模板；返回的Golden SQL不经过LLM改写。",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    print(f"report={REPORT}")
    return 0 if not failures and collection.count() == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
