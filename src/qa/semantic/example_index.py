"""Dedicated vector index for mapping SQL questions to metric contracts."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PERSIST_DIR = PROJECT_ROOT / "data" / "vector_store"
FIXTURE_PATH = (
    PROJECT_ROOT
    / "src"
    / "tests"
    / "fixtures"
    / "sql_semantic_benchmark.jsonl"
)
COLLECTION_NAME = "sql_metric_examples"
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
MAX_COSINE_DISTANCE = 0.26


def load_semantic_examples() -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in FIXTURE_PATH.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]


@lru_cache(maxsize=1)
def _examples_by_id() -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in load_semantic_examples()}


@lru_cache(maxsize=1)
def _embedding_function():
    from chromadb.utils.embedding_functions import (
        SentenceTransformerEmbeddingFunction,
    )

    return SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL,
        device="cpu",
    )


def _client():
    import chromadb

    PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(PERSIST_DIR))


@lru_cache(maxsize=1)
def get_semantic_example_collection():
    return _client().get_collection(
        name=COLLECTION_NAME,
        embedding_function=_embedding_function(),
    )


def rebuild_semantic_example_index() -> int:
    """Synchronize the collection from the versioned 50-case fixture."""
    client = _client()
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=_embedding_function(),
        metadata={
            "hnsw:space": "cosine",
            "purpose": "sql_metric_resolution",
        },
    )
    existing_ids = collection.get(include=[])["ids"]
    if existing_ids:
        collection.delete(ids=existing_ids)
    cases = load_semantic_examples()
    collection.add(
        ids=[f"sql_metric_{case['id']}" for case in cases],
        documents=[case["question"] for case in cases],
        metadatas=[
            {
                "case_id": case["id"],
                "metric_id": case["expectedPlan"]["metricId"],
                "fact_table": case["expectedPlan"]["factTable"],
                "dialect": case["dialect"],
                "source": case["source"],
                "time_scope": case["expectedPlan"].get("timeScope") or "",
                "time_basis": case["expectedPlan"].get("timeBasis") or "",
                "golden_sql": case["goldenSql"],
            }
            for case in cases
        ],
    )
    get_semantic_example_collection.cache_clear()
    return collection.count()


def query_metric_examples(
    question: str,
    *,
    dialect: str | None = None,
    time_scope: str | None = None,
    time_basis: str | None = None,
    n_results: int = 3,
) -> list[dict[str, Any]]:
    """Return nearest metric examples without accepting a metric automatically."""
    try:
        collection = get_semantic_example_collection()
        count = collection.count()
        if not count:
            return []
        filters = []
        if dialect:
            filters.append({"dialect": dialect.lower()})
        if time_scope and time_scope != "未指定":
            filters.append({"time_scope": time_scope})
        if time_basis:
            filters.append({"time_basis": time_basis})
        where = None
        if len(filters) == 1:
            where = filters[0]
        elif filters:
            where = {"$and": filters}

        result = collection.query(
            query_texts=[question],
            n_results=min(n_results, count),
            where=where,
            include=["documents", "metadatas", "distances"],
        )
    except Exception:
        return []

    documents = (result.get("documents") or [[]])[0]
    metadatas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]
    return [
        {
            "question": document,
            "distance": float(distance),
            **(metadata or {}),
        }
        for document, metadata, distance in zip(
            documents,
            metadatas,
            distances,
        )
    ]


def resolve_metric_id_semantically(
    question: str,
    *,
    dialect: str | None = None,
    max_distance: float = MAX_COSINE_DISTANCE,
) -> str | None:
    """Accept only a close match whose nearest examples agree on the metric."""
    matches = query_metric_examples(
        question,
        dialect=dialect,
        n_results=3,
    )
    if not matches or matches[0]["distance"] > max_distance:
        return None

    nearest_metric = matches[0].get("metric_id")
    close_matches = [
        item
        for item in matches
        if item["distance"] <= min(max_distance, matches[0]["distance"] + 0.05)
    ]
    if any(
        item.get("metric_id") != nearest_metric
        for item in close_matches
    ):
        return None
    return nearest_metric


def resolve_static_sql_example(
    question: str,
    *,
    dialect: str,
    metric_id: str | None = None,
    time_scope: str | None = None,
    time_basis: str | None = None,
    max_distance: float = MAX_COSINE_DISTANCE,
) -> dict[str, Any] | None:
    """Resolve one immutable Golden SQL entry from natural language."""
    matches = query_metric_examples(
        question,
        dialect=dialect,
        time_scope=time_scope,
        time_basis=time_basis,
        n_results=3,
    )
    if not matches:
        return None
    nearest = matches[0]
    if nearest["distance"] > max_distance:
        return None
    if metric_id and nearest.get("metric_id") != metric_id:
        return None

    case = _examples_by_id().get(nearest.get("case_id", ""))
    if not case:
        return None
    if (
        nearest.get("golden_sql") != case.get("goldenSql")
        or nearest.get("metric_id")
        != case.get("expectedPlan", {}).get("metricId")
        or nearest.get("dialect") != case.get("dialect")
    ):
        return None
    return {
        **nearest,
        "golden_sql": case["goldenSql"],
        "expected_plan": case["expectedPlan"],
    }
