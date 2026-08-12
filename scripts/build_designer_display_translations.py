#!/usr/bin/env python3
"""Build bilingual display descriptions without changing graph structure.

English descriptions come from Camstar Designer first, then local Swagger.
Chinese descriptions are translated from that English source. Items without an
English metadata source retain their existing Chinese description and receive
an English translation. The output contains descriptions only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "src" / "ontology" / "display_translations.json"
DEFAULT_SWAGGER = PROJECT_ROOT / "src" / "Swagger"
DEFAULT_CACHE = Path(tempfile.gettempdir()) / "camstar-description-translation-cache.json"
SWAGGER_MARKER = "【Swagger】"
CHINESE_RE = re.compile(r"[\u3400-\u9fff]")


def compact(value: Any) -> str:
    return " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split())


def clean_existing_chinese(value: str) -> str:
    text = compact(value)
    if SWAGGER_MARKER in text:
        text = text.split(SWAGGER_MARKER, 1)[0].strip()
    return text


def load_designer(path: Path) -> dict[str, dict[str, Any]]:
    rows = json.loads(path.read_text(encoding="utf-8-sig"))
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        name = compact(row.get("cdoName"))
        if not name:
            continue
        item = result.setdefault(
            name.casefold(),
            {"name": name, "description": compact(row.get("cdoDescription")), "fields": {}},
        )
        field_name = compact(row.get("fieldName"))
        if field_name:
            item["fields"][field_name.casefold()] = compact(row.get("fieldDescription"))
    return result


def designer_match(class_name: str, catalog: dict[str, dict[str, Any]]) -> tuple[dict[str, Any] | None, str]:
    exact = catalog.get(class_name.casefold())
    if exact:
        return exact, "designer_exact"
    if class_name.startswith("A_"):
        normalized = catalog.get(class_name[2:].casefold())
        if normalized:
            return normalized, "designer_A_prefix"
    return None, ""


def load_cache(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_cache(path: Path, cache: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def translate_batch(client: OpenAI, model: str, direction: str, values: list[str]) -> list[str]:
    rows = {str(index): value for index, value in enumerate(values)}
    if direction == "en_to_zh":
        instruction = (
            "你是 Siemens Opcenter Execution（Camstar）MES 术语专家。"
            "将每条英文对象或字段说明忠实翻译成简洁准确的简体中文。"
            "不得修改技术标识符、产品名、缩写、枚举值和引用类型，不得补造功能。"
            "仅返回 JSON 对象，键必须与输入完全一致，值为中文说明。"
        )
    else:
        instruction = (
            "You are a Siemens Opcenter Execution (Camstar) MES terminology expert. "
            "Translate each Chinese object or field description into concise, accurate English. "
            "Preserve identifiers, product names, abbreviations, enum values, and referenced types. "
            "Do not invent behavior. Return only a JSON object with exactly the input keys."
        )
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": instruction},
            {"role": "user", "content": json.dumps(rows, ensure_ascii=False)},
        ],
    )
    parsed = json.loads(response.choices[0].message.content or "{}")
    if set(parsed) != set(rows):
        raise ValueError("Translation response keys do not match the input batch")
    result = [compact(parsed[str(index)]) for index in range(len(values))]
    if any(not value for value in result):
        raise ValueError("Translation response contains an empty description")
    return result


def translate_values(
    client: OpenAI,
    model: str,
    direction: str,
    values: list[str],
    cache: dict[str, str],
    cache_path: Path,
    batch_size: int,
    workers: int,
) -> dict[str, str]:
    unique = list(dict.fromkeys(compact(value) for value in values if compact(value)))
    pending = [value for value in unique if f"{direction}\n{value}" not in cache]
    batches = [pending[index:index + batch_size] for index in range(0, len(pending), batch_size)]
    def run_batch(index: int, batch: list[str]) -> tuple[int, list[str], list[str]]:
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                translated = translate_batch(client, model, direction, batch)
                return index, batch, translated
            except Exception as exc:  # network/model errors are retried with a short backoff
                last_error = exc
                time.sleep(2 * (attempt + 1))
        assert last_error is not None
        raise last_error

    if batches:
        print(
            f"translation_direction={direction} batches={len(batches)} workers={min(workers, len(batches))}",
            flush=True,
        )
    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        futures = {
            executor.submit(run_batch, index, batch): index
            for index, batch in enumerate(batches, start=1)
        }
        for completed, future in enumerate(as_completed(futures), start=1):
            index, batch, translated = future.result()
            for source, target in zip(batch, translated):
                cache[f"{direction}\n{source}"] = target
            save_cache(cache_path, cache)
            print(
                f"translation_direction={direction} completed={completed}/{len(batches)} batch={index}",
                flush=True,
            )
    return {value: cache[f"{direction}\n{value}"] for value in unique}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--designer-export", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--no-translate", action="store_true")
    args = parser.parse_args()

    import sys

    sys.path.insert(0, str(PROJECT_ROOT))
    from scripts.align_swagger_field_translations import find_swagger_source, load_swagger_index
    from web.routers.i18n import _graph_catalog_snapshot

    graph_nodes, graph_details = _graph_catalog_snapshot()
    designer = load_designer(args.designer_export)
    swagger = load_swagger_index(DEFAULT_SWAGGER)

    node_rows: list[dict[str, str]] = []
    property_rows: list[dict[str, str]] = []
    stats = {
        "nodes": len(graph_nodes),
        "properties": 0,
        "nodeDesignerExact": 0,
        "nodeDesignerAPrefix": 0,
        "nodeFallback": 0,
        "propertyDesigner": 0,
        "propertySwagger": 0,
        "propertyFallback": 0,
    }

    for node in graph_nodes:
        class_name = node["key"]
        matched, source_kind = designer_match(class_name, designer)
        english = compact(matched.get("description")) if matched else ""
        chinese = clean_existing_chinese(node.get("descriptionZh", ""))
        if english:
            stats["nodeDesignerExact" if source_kind == "designer_exact" else "nodeDesignerAPrefix"] += 1
        else:
            stats["nodeFallback"] += 1
        node_rows.append({"key": class_name, "en": english, "zh": chinese})

        for prop in graph_details.get(class_name, {}).get("properties", []):
            stats["properties"] += 1
            property_name = compact(prop.get("name"))
            key = f"{class_name}.{property_name}"
            english = ""
            if matched:
                english = compact(matched["fields"].get(property_name.casefold()))
            if english:
                stats["propertyDesigner"] += 1
            else:
                swagger_source = find_swagger_source(class_name, property_name, swagger)
                if swagger_source and swagger_source.source_text:
                    english = compact(swagger_source.source_text)
                    if swagger_source.source_kind == "reference" and english.lower().startswith("referenced schema"):
                        target = english.split(":", 1)[-1].strip()
                        english = f"References {target}."
                    stats["propertySwagger"] += 1
                else:
                    source_description = compact(prop.get("description"))
                    if SWAGGER_MARKER in source_description:
                        candidate = source_description.split(SWAGGER_MARKER, 1)[1].strip()
                        if candidate and not candidate.startswith("引用 Schema"):
                            english = candidate
                            stats["propertySwagger"] += 1
            if not english:
                stats["propertyFallback"] += 1
            property_rows.append(
                {
                    "key": key,
                    "en": english,
                    "zh": clean_existing_chinese(prop.get("description", "")),
                }
            )

    if stats["nodes"] != 593 or stats["properties"] != 8337:
        raise RuntimeError(f"Graph snapshot changed unexpectedly: {stats}")

    cache = load_cache(args.cache)
    if not args.no_translate:
        load_dotenv(PROJECT_ROOT / ".env")
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is missing")
        client = OpenAI(
            api_key=api_key,
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            timeout=float(os.getenv("LLM_TIMEOUT", "120")),
        )
        model = os.getenv("LLM_MODEL", "deepseek-chat")
        english_sources = [row["en"] for row in node_rows + property_rows if row["en"]]
        en_to_zh = translate_values(
            client, model, "en_to_zh", english_sources, cache, args.cache, args.batch_size, args.workers
        )
        chinese_sources = [row["zh"] for row in node_rows + property_rows if not row["en"] and row["zh"]]
        zh_to_en = translate_values(
            client, model, "zh_to_en", chinese_sources, cache, args.cache, args.batch_size, args.workers
        )
        for row in node_rows + property_rows:
            if row["en"]:
                row["zh"] = en_to_zh[row["en"]]
            elif row["zh"]:
                row["en"] = zh_to_en[row["zh"]]

    incomplete = [row["key"] for row in node_rows + property_rows if not row["zh"] or not row["en"]]
    if incomplete:
        raise RuntimeError(f"Descriptions remain incomplete: {incomplete[:20]} (total {len(incomplete)})")

    # Designer occasionally uses only a type/identifier (for example String40
    # or CAPA) as the description. Keep that technical token while making the
    # Chinese display explicit instead of leaving it looking untranslated.
    for row in node_rows:
        if not CHINESE_RE.search(row["zh"]):
            token = row["zh"].strip().rstrip("。") or row["key"]
            row["zh"] = f"Camstar {token} 对象。"
    for row in property_rows:
        if not CHINESE_RE.search(row["zh"]):
            token = row["zh"].strip().rstrip("。") or row["key"].rsplit(".", 1)[-1]
            string_type = re.fullmatch(r"String(\d+)", token, re.IGNORECASE)
            if string_type:
                row["zh"] = f"最长 {string_type.group(1)} 个字符的字符串字段。"
            else:
                row["zh"] = f"{token} 技术字段。"

    output = {
        "version": 1,
        "revision": int(time.time()),
        "updatedAt": int(time.time() * 1000),
        "translations": {
            "nodeDescriptions": {row["key"]: {"zh": row["zh"], "en": row["en"]} for row in node_rows},
            "propertyDescriptions": {row["key"]: {"zh": row["zh"], "en": row["en"]} for row in property_rows},
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(args.output)
    print(json.dumps(stats, ensure_ascii=False), flush=True)
    print(f"output={args.output.resolve()}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
