#!/usr/bin/env python3
"""Align placeholder ontology field descriptions with local Swagger schemas.

Only descriptions beginning with ``物理字段 `` are eligible for replacement.
Class matching is intentionally conservative: an ontology class must match a
Swagger schema named ``<ClassName>Entity`` or ``<ClassName>`` (with an
additional reviewed convention for the ``A_`` physical prefix), and the
property name must match exactly.

Swagger descriptions contain English Camstar annotations.  ``--translate``
uses the configured project LLM to translate the matched source text and saves
an auditable cache.  ``--apply`` then replaces placeholder descriptions with
cached Chinese descriptions without touching existing hand-written content.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ONTOLOGY_DIR = PROJECT_ROOT / "src" / "ontology" / "wiki_kb"
DEFAULT_SWAGGER_DIR = PROJECT_ROOT / "src" / "Swagger"
DEFAULT_CACHE = PROJECT_ROOT / "src" / "ontology" / "swagger_field_translations.json"
DEFAULT_REPORT = PROJECT_ROOT / "docs" / "swagger_field_translation_report.md"
DEFAULT_UNRESOLVED_CSV = (
    PROJECT_ROOT / "docs" / "swagger_unresolved_field_translations.csv"
)
PLACEHOLDER_PREFIX = "物理字段 "
STANDARD_PROPERTY_TRANSLATIONS = {
    "associatedPackages": "关联变更包的数量。",
    "setupAccess": "关联的建模访问权限（A_SetupAccess）。",
    "changeHistory": "关联的变更历史记录（ChangeStatus）。",
    "description": "实体说明；未指定时默认使用实体名称。",
    "eco": "工程变更单（ECO）。",
    "filterTags": "以逗号分隔的筛选标签列表。",
    "iconId": "关联图标的标识符。",
    "instanceLocked": "是否已被变更管理锁定。",
    "isFrozen": "是否已冻结；冻结后不允许修改该实例或其修订。",
    "notes": "与该对象相关的备注和注释。",
    "wipMsgDefMgr": "关联的WIP消息定义管理器（WIPMsgDefMgr）。",
}
ANNOTATION_RE = re.compile(
    r"Annotations:\s*(.*?)(?:;\s*OriginalType:|$)",
    re.IGNORECASE | re.DOTALL,
)


@dataclass(frozen=True)
class SwaggerSource:
    schema_name: str
    property_name: str
    source_text: str
    source_kind: str
    files: tuple[str, ...]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def compact_text(value: str) -> str:
    return " ".join(value.replace("\r", " ").replace("\n", " ").split())


def annotation_text(description: str) -> str:
    match = ANNOTATION_RE.search(description)
    if not match:
        return compact_text(description)
    return compact_text(match.group(1))


def ref_target(prop: dict[str, Any]) -> str:
    ref = prop.get("$ref") or prop.get("items", {}).get("$ref", "")
    return ref.rsplit("/", 1)[-1] if ref else ""


def schema_candidates(class_name: str) -> list[str]:
    result = [f"{class_name}Entity", class_name]
    if class_name.startswith("A_"):
        physical_name = class_name[2:]
        result.extend([f"{physical_name}Entity", physical_name])
    return list(dict.fromkeys(result))


def load_swagger_index(swagger_dir: Path) -> dict[str, list[tuple[str, dict[str, Any]]]]:
    index: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    for path in sorted(swagger_dir.glob("*.json")):
        payload = read_json(path)
        for schema_name, schema in (
            payload.get("components", {}).get("schemas", {}).items()
        ):
            index[schema_name].append((path.name, schema))
    return index


def find_swagger_source(
    class_name: str,
    property_name: str,
    index: dict[str, list[tuple[str, dict[str, Any]]]],
) -> SwaggerSource | None:
    for schema_name in schema_candidates(class_name):
        occurrences = index.get(schema_name, [])
        matched: list[tuple[str, dict[str, Any]]] = []
        for file_name, schema in occurrences:
            prop = schema.get("properties", {}).get(property_name)
            if prop is not None:
                matched.append((file_name, prop))
        if not matched:
            continue

        annotations = [
            annotation_text(prop.get("description", ""))
            for _, prop in matched
            if prop.get("description")
        ]
        annotations = list(dict.fromkeys(text for text in annotations if text))
        if annotations:
            # Repeated modeling Swagger files commonly contain the same schema.
            # Reject disagreement instead of selecting an arbitrary description.
            if len(annotations) != 1:
                return None
            source_text = annotations[0]
            source_kind = "annotation"
        else:
            targets = list(
                dict.fromkeys(
                    target
                    for _, prop in matched
                    if (target := ref_target(prop))
                )
            )
            if len(targets) != 1:
                return None
            source_text = f"Swagger reference target: {targets[0]}"
            source_kind = "reference"

        return SwaggerSource(
            schema_name=schema_name,
            property_name=property_name,
            source_text=source_text,
            source_kind=source_kind,
            files=tuple(sorted({file_name for file_name, _ in matched})),
        )
    return None


def collect_candidates(
    ontology_dir: Path,
    swagger_index: dict[str, list[tuple[str, dict[str, Any]]]],
    cached: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    candidates: list[dict[str, Any]] = []
    stats = {
        "ontology_files": 0,
        "ontology_classes": 0,
        "ontology_properties": 0,
        "placeholder_properties": 0,
        "swagger_matches": 0,
        "swagger_annotation_matches": 0,
        "swagger_reference_matches": 0,
    }
    for path in sorted(ontology_dir.glob("*_ontology.json")):
        payload = read_json(path)
        stats["ontology_files"] += 1
        for class_item in payload.get("classes", []):
            stats["ontology_classes"] += 1
            class_name = class_item["className"]
            for prop in class_item.get("properties", []):
                stats["ontology_properties"] += 1
                item_id = f"{class_name}.{prop['name']}"
                old_description = prop.get("description", "")
                is_placeholder = old_description.startswith(PLACEHOLDER_PREFIX)
                if is_placeholder:
                    stats["placeholder_properties"] += 1
                if not is_placeholder and item_id not in cached:
                    continue
                source = find_swagger_source(
                    class_name,
                    prop["name"],
                    swagger_index,
                )
                if source is None:
                    continue
                stats["swagger_matches"] += 1
                stats[f"swagger_{source.source_kind}_matches"] += 1
                candidates.append(
                    {
                        "id": item_id,
                        "className": class_name,
                        "propertyName": prop["name"],
                        "physicalDescription": (
                            old_description
                            if is_placeholder
                            else cached[item_id]["physicalDescription"]
                        ),
                        "swaggerSchema": source.schema_name,
                        "swaggerSourceKind": source.source_kind,
                        "swaggerSource": source.source_text,
                        "swaggerFiles": list(source.files),
                        "ontologyFile": path.name,
                    }
                )
    return candidates, stats


def load_cache(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    payload = read_json(path)
    return {
        item["id"]: item
        for item in payload.get("translations", [])
        if item.get("id") and item.get("descriptionZh")
    }


def translation_batches(
    candidates: list[dict[str, Any]],
    cached: dict[str, dict[str, Any]],
    batch_size: int,
    refresh_references: bool,
) -> list[list[dict[str, Any]]]:
    pending = [
        item
        for item in candidates
        if (
            refresh_references
            and item["swaggerSourceKind"] == "reference"
        )
        or item["id"] not in cached
        or cached[item["id"]].get("swaggerSource") != item["swaggerSource"]
    ]
    return [
        pending[index : index + batch_size]
        for index in range(0, len(pending), batch_size)
    ]


def translate_batch(
    client: OpenAI,
    model: str,
    batch: list[dict[str, Any]],
) -> dict[str, str]:
    input_rows = [
        {
            "id": item["id"],
            "className": item["className"],
            "propertyName": item["propertyName"],
            "physicalDescription": item["physicalDescription"],
            "swaggerSourceKind": item["swaggerSourceKind"],
            "swaggerSource": item["swaggerSource"],
        }
        for item in batch
    ]
    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "你是 Siemens Opcenter Execution（Camstar）MES 字段术语翻译专家。"
                    "把 Swagger 英文注释翻译成简洁、准确的中文字段说明。"
                    "必须忠实于输入，不补造功能；保留产品名、缩写、枚举数值、"
                    "CDO、WIP、UOM、ROR 等技术术语。引用目标类型应表述为"
                    "“关联的……”。当 swaggerSourceKind 为 reference 时，"
                    "physicalDescription 中箭头右侧的物理外键目标是业务目标，"
                    "应优先据此和 propertyName 描述字段；NamedObjectRef、"
                    "RevisionedObjectRef、NamedSubentityRef 等只是 API 包装类型，"
                    "有物理目标时不得把它们写进中文说明。"
                    "每条说明通常 8–45 个汉字；只有原文确实复杂时才可更长。"
                    "返回 JSON 对象，键为输入 id，值为中文说明，不得遗漏或增加键。"
                ),
            },
            {
                "role": "user",
                "content": json.dumps(input_rows, ensure_ascii=False),
            },
        ],
    )
    content = response.choices[0].message.content or "{}"
    result = json.loads(content)
    expected = {item["id"] for item in batch}
    if set(result) != expected:
        missing = sorted(expected - set(result))
        extra = sorted(set(result) - expected)
        raise ValueError(
            f"Translation response keys differ; missing={missing}, extra={extra}"
        )
    cleaned: dict[str, str] = {}
    for item_id, value in result.items():
        if not isinstance(value, str):
            raise ValueError(f"Translation for {item_id} is not a string")
        value = compact_text(value).strip("。") + "。"
        if not re.search(r"[\u4e00-\u9fff]", value):
            raise ValueError(f"Translation for {item_id} contains no Chinese text")
        if value.startswith(PLACEHOLDER_PREFIX):
            raise ValueError(f"Translation for {item_id} is still a placeholder")
        cleaned[item_id] = value
    return cleaned


def save_cache(
    path: Path,
    candidates: list[dict[str, Any]],
    cached: dict[str, dict[str, Any]],
) -> None:
    translations = []
    for candidate in sorted(candidates, key=lambda item: item["id"]):
        item = dict(candidate)
        existing = cached.get(candidate["id"], {})
        if existing.get("descriptionZh"):
            item["descriptionZh"] = existing["descriptionZh"]
            translations.append(item)
    path.write_text(
        json.dumps(
            {
                "source": "Local OpenAPI Swagger annotations",
                "matchingRule": (
                    "<ClassName>Entity or <ClassName> schema plus exact property name"
                ),
                "translations": translations,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def normalize_cached_translations(
    cached: dict[str, dict[str, Any]],
) -> int:
    """Apply project-wide Camstar terminology to repeated inherited fields."""
    changed = 0
    for item in cached.values():
        standard = STANDARD_PROPERTY_TRANSLATIONS.get(item.get("propertyName", ""))
        if standard and item.get("descriptionZh") != standard:
            item["descriptionZh"] = standard
            changed += 1
    return changed


def apply_translations(
    ontology_dir: Path,
    cached: dict[str, dict[str, Any]],
    previous_descriptions: dict[str, str],
) -> tuple[int, int]:
    files_changed = 0
    properties_changed = 0
    for path in sorted(ontology_dir.glob("*_ontology.json")):
        payload = read_json(path)
        changed = False
        for class_item in payload.get("classes", []):
            class_name = class_item["className"]
            for prop in class_item.get("properties", []):
                item_id = f"{class_name}.{prop['name']}"
                translation = cached.get(item_id)
                current_description = prop.get("description", "")
                if (
                    translation
                    and (
                        current_description.startswith(PLACEHOLDER_PREFIX)
                        or current_description == previous_descriptions.get(item_id)
                    )
                    and current_description != translation["descriptionZh"]
                ):
                    prop["description"] = translation["descriptionZh"]
                    changed = True
                    properties_changed += 1
        if changed:
            path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            files_changed += 1
    return files_changed, properties_changed


def write_report(
    path: Path,
    stats: dict[str, int],
    candidates: list[dict[str, Any]],
    cached: dict[str, dict[str, Any]],
    files_changed: int,
    properties_changed: int,
) -> None:
    translated = sum(1 for item in candidates if item["id"] in cached)
    unresolved = stats["placeholder_properties"]
    by_class: dict[str, int] = defaultdict(int)
    for item in candidates:
        if item["id"] in cached:
            by_class[item["className"]] += 1
    top_classes = sorted(by_class.items(), key=lambda item: (-item[1], item[0]))

    lines = [
        "# Swagger 字段翻译对齐报告",
        "",
        "本报告仅统计原说明以 `物理字段 ` 开头的占位字段。已有人工说明未被覆盖。",
        "",
        "## 汇总",
        "",
        "| 指标 | 数量 |",
        "|---|---:|",
        f"| 本体属性 | {stats['ontology_properties']} |",
        f"| 当前剩余占位字段 | {stats['placeholder_properties']} |",
        f"| Swagger 强匹配 | {stats['swagger_matches']} |",
        f"| 其中：英文注释匹配 | {stats['swagger_annotation_matches']} |",
        f"| 其中：引用目标匹配 | {stats['swagger_reference_matches']} |",
        f"| 已对齐中文字段 | {translated} |",
        f"| 仍待其他资料补充 | {unresolved} |",
        "",
        "## 匹配规则",
        "",
        "- 类名仅匹配 Swagger 的 `<ClassName>Entity` 或 `<ClassName>` schema。",
        "- `A_` 前缀物理类额外允许匹配去前缀后的同名 schema。",
        "- 属性名必须完全一致；不使用全局 FieldId，避免不同 CDO 复用 FieldId 导致错配。",
        "- 仅替换占位说明，不覆盖现有人工中文说明。",
        "",
        "## 已对齐字段最多的类",
        "",
        "| 类 | 字段数 |",
        "|---|---:|",
    ]
    lines.extend(f"| `{name}` | {count} |" for name, count in top_classes[:40])
    lines += [
        "",
        "完整的 Swagger 原文、来源文件和中文结果保存在 "
        "`src/ontology/swagger_field_translations.json`。",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_unresolved_csv(
    path: Path,
    ontology_dir: Path,
    swagger_index: dict[str, list[tuple[str, dict[str, Any]]]],
) -> int:
    rows: list[dict[str, str]] = []
    for ontology_path in sorted(ontology_dir.glob("*_ontology.json")):
        payload = read_json(ontology_path)
        for class_item in payload.get("classes", []):
            class_name = class_item["className"]
            matching_schemas = [
                name
                for name in schema_candidates(class_name)
                if name in swagger_index
            ]
            reason = (
                "property_not_exposed_or_name_differs"
                if matching_schemas
                else "no_matching_swagger_schema"
            )
            for prop in class_item.get("properties", []):
                description = prop.get("description", "")
                if not description.startswith(PLACEHOLDER_PREFIX):
                    continue
                rows.append(
                    {
                        "ontologyFile": ontology_path.name,
                        "module": payload.get("module", ""),
                        "className": class_name,
                        "chineseName": class_item.get("chineseName", ""),
                        "propertyName": prop["name"],
                        "propertyType": prop.get("type", ""),
                        "physicalDescription": description,
                        "matchingSwaggerSchemas": ",".join(matching_schemas),
                        "reason": reason,
                    }
                )
    fieldnames = [
        "ontologyFile",
        "module",
        "className",
        "chineseName",
        "propertyName",
        "propertyType",
        "physicalDescription",
        "matchingSwaggerSchemas",
        "reason",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ontology-dir", type=Path, default=DEFAULT_ONTOLOGY_DIR)
    parser.add_argument("--swagger-dir", type=Path, default=DEFAULT_SWAGGER_DIR)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--unresolved-csv",
        type=Path,
        default=DEFAULT_UNRESOLVED_CSV,
    )
    parser.add_argument("--batch-size", type=int, default=40)
    parser.add_argument("--translate", action="store_true")
    parser.add_argument(
        "--refresh-references",
        action="store_true",
        help="Retranslate cached Swagger reference matches using physical FK targets",
    )
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    swagger_index = load_swagger_index(args.swagger_dir)
    cached = load_cache(args.cache)
    previous_descriptions = {
        item_id: item["descriptionZh"]
        for item_id, item in cached.items()
        if item.get("descriptionZh")
    }
    normalized_cached = normalize_cached_translations(cached)
    candidates, stats = collect_candidates(args.ontology_dir, swagger_index, cached)

    if args.translate:
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
        batches = translation_batches(
            candidates,
            cached,
            args.batch_size,
            args.refresh_references,
        )
        for index, batch in enumerate(batches, start=1):
            print(f"translating_batch={index}/{len(batches)} size={len(batch)}")
            translated = translate_batch(client, model, batch)
            for candidate in batch:
                cached[candidate["id"]] = {
                    **candidate,
                    "descriptionZh": translated[candidate["id"]],
                }
            save_cache(args.cache, candidates, cached)

    normalized_cached += normalize_cached_translations(cached)
    if normalized_cached:
        save_cache(args.cache, candidates, cached)

    files_changed = 0
    properties_changed = 0
    if args.apply:
        files_changed, properties_changed = apply_translations(
            args.ontology_dir,
            cached,
            previous_descriptions,
        )

    write_report(
        args.report,
        stats,
        candidates,
        cached,
        files_changed,
        properties_changed,
    )
    unresolved_rows = write_unresolved_csv(
        args.unresolved_csv,
        args.ontology_dir,
        swagger_index,
    )
    print(json.dumps(stats, ensure_ascii=False))
    print(f"cached_translations={len(cached)}")
    print(f"normalized_cached_translations={normalized_cached}")
    print(f"files_changed={files_changed}")
    print(f"properties_changed={properties_changed}")
    print(f"unresolved_rows={unresolved_rows}")
    print(f"cache={args.cache}")
    print(f"report={args.report}")
    print(f"unresolved_csv={args.unresolved_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
