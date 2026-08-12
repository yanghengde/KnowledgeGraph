"""
Wiki Manager – Relationship Wiki Knowledge Base Engine
──────────────────────────────────────────────────────
Manages per-product-line Markdown wiki files for each ontology relationship.
Supports:
  • Read / Write / Update individual wiki files
  • Batch generation via LLM (DeepSeek)
  • Product-line isolation
  • Collect all relationships from ontology JSONs
"""
import os
import csv
import json
import glob
import re
import time
from datetime import datetime
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv(override=True)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WIKI_KB_PATH = os.path.join(PROJECT_ROOT, "src", "ontology", "wiki_kb")
RELATIONSHIPS_DIR = os.path.join(WIKI_KB_PATH, "relationships")
PRODUCT_LINES_FILE = os.path.join(WIKI_KB_PATH, "product_lines.json")
DATABASE_FIELDS_FILE = os.path.join(PROJECT_ROOT, "docs", "Database_Fields.csv")

# LLM config
API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "120"))

# Wiki review flag (for future use)
WIKI_REVIEW_REQUIRED = os.getenv("WIKI_REVIEW_REQUIRED", "false").lower() == "true"

_llm_client = None


def _get_llm():
    global _llm_client
    if _llm_client is None:
        from openai import OpenAI
        _llm_client = OpenAI(api_key=API_KEY, base_url=BASE_URL, timeout=LLM_TIMEOUT)
    return _llm_client


# ══════════════════════════════════════════════════════
#  Product Line Helpers
# ══════════════════════════════════════════════════════

def load_product_lines() -> list[dict]:
    """Load all product line definitions from product_lines.json."""
    try:
        with open(PRODUCT_LINES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("product_lines", [])
    except Exception as e:
        print(f"[WikiManager] Error loading product lines: {e}")
        return [{"id": "general", "name": "通用", "description": "", "icon": "📦", "color": "#009999"}]


def save_product_lines(product_lines: list[dict]) -> bool:
    """Save all product line definitions to product_lines.json."""
    try:
        with open(PRODUCT_LINES_FILE, "w", encoding="utf-8") as f:
            json.dump({"product_lines": product_lines}, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"[WikiManager] Error saving product lines: {e}")
        return False


def get_product_line_info(product_line_id: str) -> dict:
    """Get a single product line's info by ID."""
    for pl in load_product_lines():
        if pl["id"] == product_line_id:
            return pl
    return {"id": product_line_id, "name": product_line_id, "description": "", "icon": "📦", "color": "#999"}


# ══════════════════════════════════════════════════════
#  Relationship Collection
# ══════════════════════════════════════════════════════

def collect_all_relationships() -> list[dict]:
    """
    Scan all *_ontology.json files (including cross_module_ontology.json)
    and return a unified list of relationships.
    Each item: { fromClass, toClass, relationName, cardinality, description, source_file }
    """
    relationships = []
    seen_keys = set()

    json_files = glob.glob(os.path.join(WIKI_KB_PATH, "*_ontology.json"))
    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            source = os.path.basename(file_path)
            for rel in data.get("relationships", []):
                key = f"{rel['fromClass']}_{rel['relationName']}_{rel['toClass']}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    relationships.append({
                        "fromClass": rel["fromClass"],
                        "toClass": rel["toClass"],
                        "relationName": rel["relationName"],
                        "cardinality": rel.get("cardinality", ""),
                        "description": rel.get("description", ""),
                        "source_file": source,
                    })
        except Exception as e:
            print(f"[WikiManager] Error reading {file_path}: {e}")

    return relationships


# ══════════════════════════════════════════════════════
#  Wiki File Path Helpers
# ══════════════════════════════════════════════════════

def _wiki_filename(from_class: str, rel_name: str, to_class: str) -> str:
    """Generate wiki filename: {From}_{Rel}_{To}.md"""
    return f"{from_class}_{rel_name}_{to_class}.md"


def _wiki_filepath(product_line: str, from_class: str, rel_name: str, to_class: str) -> str:
    """Full filesystem path for a wiki file."""
    filename = _wiki_filename(from_class, rel_name, to_class)
    return os.path.join(RELATIONSHIPS_DIR, product_line, filename)


def _ensure_product_dir(product_line: str):
    """Ensure the product line directory exists."""
    dirpath = os.path.join(RELATIONSHIPS_DIR, product_line)
    os.makedirs(dirpath, exist_ok=True)


# ══════════════════════════════════════════════════════
#  Wiki CRUD Operations
# ══════════════════════════════════════════════════════

def read_wiki(
    product_line: str,
    from_class: str,
    rel_name: str,
    to_class: str,
    sql_dialect: str = "oracle",
) -> dict:
    """
    Read a wiki file. Returns:
      { found: bool, content: str, sql_content: str, path: str, metadata: dict }

    ``content`` is reserved for authored relationship usage. Deterministic SQL
    is returned separately through ``sql_content`` so a physical-schema-only
    document does not masquerade as an authored Wiki.
    """
    filepath = _wiki_filepath(product_line, from_class, rel_name, to_class)
    relationship = get_relationship_definition(from_class, rel_name, to_class)
    sql_content = (
        build_relationship_sql_section(
            from_class,
            rel_name,
            to_class,
            relationship.get("description", ""),
            sql_dialect=sql_dialect,
        )
        if relationship
        else ""
    )

    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        authored = _wiki_has_authored_content(filepath, content)
        content = strip_relationship_sql_section(content) if authored else ""

        # Extract metadata from YAML-like header if present
        metadata = _extract_metadata(content)
        
        # Check review status
        if WIKI_REVIEW_REQUIRED and metadata.get("status") != "approved":
            return {
                "found": False,
                "content": "",
                "sql_content": sql_content,
                "path": filepath,
                "metadata": metadata,
                "reason": "pending_review",
            }

        return {
            "found": bool(content.strip()),
            "content": content,
            "sql_content": sql_content,
            "path": filepath,
            "metadata": metadata,
            "product_line": product_line,
            "reason": "" if content.strip() else "relationship_wiki_missing",
        }

    # A product-line-specific Wiki may be absent while an authored general Wiki
    # already exists. Reuse only its relationship-usage body; SQL stays separate.
    if product_line != "general":
        general_path = _wiki_filepath("general", from_class, rel_name, to_class)
        if os.path.exists(general_path):
            with open(general_path, "r", encoding="utf-8") as f:
                content = f.read()
            if _wiki_has_authored_content(general_path, content):
                content = strip_relationship_sql_section(content)
                return {
                    "found": bool(content.strip()),
                    "content": content,
                    "sql_content": sql_content,
                    "path": general_path,
                    "metadata": {
                        **_extract_metadata(content),
                        "fallback": "general",
                    },
                    "product_line": "general",
                    "reason": "general_fallback",
                }

    return {
        "found": False,
        "content": "",
        "sql_content": sql_content,
        "path": filepath,
        "metadata": {},
        "product_line": product_line,
        "reason": "relationship_wiki_missing",
    }


def save_wiki(product_line: str, from_class: str, rel_name: str, to_class: str,
              content: str, editor: str = "system") -> dict:
    """
    Save/update a wiki file. Used by both LLM generation and manual editing.
    Adds/updates metadata header with edit history.
    """
    content = strip_relationship_sql_section(content)
    _ensure_product_dir(product_line)
    filepath = _wiki_filepath(product_line, from_class, rel_name, to_class)

    # Track edit history in a companion JSON file
    history_path = filepath.replace(".md", ".meta.json")
    history = _load_history(history_path)

    history["edits"].append({
        "editor": editor,
        "timestamp": datetime.now().isoformat(),
        "content_length": len(content),
    })
    history["last_modified"] = datetime.now().isoformat()
    history["last_editor"] = editor

    # If review is required, newly generated content starts as "draft"
    if WIKI_REVIEW_REQUIRED and editor == "llm":
        history["status"] = "draft"
    else:
        history["status"] = "approved"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    return {"saved": True, "path": filepath, "history": history}


def _load_history(history_path: str) -> dict:
    """Load or create edit history metadata."""
    if os.path.exists(history_path):
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "created": datetime.now().isoformat(),
        "last_modified": datetime.now().isoformat(),
        "last_editor": "system",
        "status": "approved",
        "edits": [],
    }


def _extract_metadata(content: str) -> dict:
    """Extract simple metadata from wiki content (first few lines with > markers)."""
    metadata = {}
    for line in content.split("\n")[:10]:
        line = line.strip()
        if line.startswith("> **") and "**:" in line:
            try:
                key = line.split("**")[1].rstrip(":")
                value = line.split("**:")[-1].strip()
                metadata[key] = value
            except Exception:
                pass
    return metadata


# ══════════════════════════════════════════════════════
#  Wiki Statistics
# ══════════════════════════════════════════════════════

def get_wiki_stats(product_line: str = None) -> dict:
    """
    Get wiki coverage statistics.
    If product_line is specified, stats for that line only.
    Otherwise, stats for all lines.
    """
    all_rels = collect_all_relationships()
    total = len(all_rels)
    product_lines = load_product_lines()

    if product_line:
        product_lines = [pl for pl in product_lines if pl["id"] == product_line]

    stats = {}
    for pl in product_lines:
        pl_id = pl["id"]
        existing = sum(
            os.path.exists(
                _wiki_filepath(
                    pl_id,
                    relationship["fromClass"],
                    relationship["relationName"],
                    relationship["toClass"],
                )
            )
            for relationship in all_rels
        )
        stats[pl_id] = {
            "name": pl["name"],
            "total_relationships": total,
            "wiki_count": existing,
            "factual_fallback_count": max(total - existing, 0),
            "available_count": total,
            "coverage": 100.0 if total > 0 else 0,
        }

    return {"product_lines": stats, "total_relationships": total}


# ══════════════════════════════════════════════════════
#  Wiki Search (for QA — wiki-first before LLM)
# ══════════════════════════════════════════════════════

def search_wiki(question: str, keywords: list[str], product_line: str = "general", top_k: int = 3) -> list[dict]:
    """
    Search relationship wiki files in the active product line (falling back to general)
    for content matching the user question.
    Returns list of {product_line, relationship, content, score} sorted by relevance.
    """
    results = []
    question_lower = question.lower()

    if not os.path.isdir(RELATIONSHIPS_DIR):
        return results

    # Only scan the selected product line and fall back to general
    dirs_to_scan = [product_line]
    if product_line != "general" and "general" not in dirs_to_scan:
        dirs_to_scan.append("general")

    for pl_dir in dirs_to_scan:
        pl_path = os.path.join(RELATIONSHIPS_DIR, pl_dir)
        if not os.path.isdir(pl_path):
            continue

        for filename in os.listdir(pl_path):
            if not filename.endswith(".md"):
                continue

            filepath = os.path.join(pl_path, filename)
            fname_lower = filename.lower()

            # Score: keyword matches in filename + content
            score = 0
            for kw in keywords:
                if kw.lower() in fname_lower:
                    score += 3  # filename match is strong signal
                if kw.lower() in question_lower:
                    score += 1

            # Also check partial class name matches
            for kw in keywords:
                parts = kw.replace("_", " ").split()
                for part in parts:
                    if len(part) >= 3 and part.lower() in fname_lower:
                        score += 1

            if score == 0:
                continue  # skip irrelevant files

            # Boost score for matches in the active product line folder
            if pl_dir == product_line:
                score += 5

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                # Boost score if question terms appear in content
                content_lower = content.lower()
                for kw in keywords:
                    if kw.lower() in content_lower:
                        score += 2

                # Parse relationship from filename: {From}_{Rel}_{To}.md
                import re
                rel_name = filename.replace(".md", "")
                match_rel = re.match(r'^([A-Z][a-zA-Z0-9]+)_([A-Z0-9_]+)_([A-Z][a-zA-Z0-9]+)$', rel_name)
                if match_rel:
                    rel_display = f"{match_rel.group(1)} → {match_rel.group(2)} → {match_rel.group(3)}"
                else:
                    parts = rel_name.split("_", 2)
                    if len(parts) >= 3:
                        rel_display = f"{parts[0]} → {parts[1]} → {parts[2]}"
                    else:
                        rel_display = rel_name

                results.append({
                    "product_line": pl_dir,
                    "relationship": rel_display,
                    "filename": filename,
                    "content": content,
                    "score": score,
                })
            except Exception:
                continue

    # Sort by score descending, take top_k
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


# ══════════════════════════════════════════════════════
#  LLM Wiki Generation
# ══════════════════════════════════════════════════════


@lru_cache(maxsize=1)
def _load_physical_fields() -> dict[str, list[dict[str, str]]]:
    """Load the immutable physical field registry, grouped by CDO name."""
    fields_by_class: dict[str, list[dict[str, str]]] = {}
    with open(DATABASE_FIELDS_FILE, "r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            fields_by_class.setdefault(row["CDOName"], []).append(row)
    return fields_by_class


SQL_DIALECTS = {"oracle", "sqlserver"}


def normalize_sql_dialect(value: str) -> str:
    """Return one of the supported deterministic SQL dialect identifiers."""
    normalized = (value or "").strip().lower()
    if normalized not in SQL_DIALECTS:
        raise ValueError(f"Unsupported SQL dialect: {value}")
    return normalized


def _sql_identifier(value: str, sql_dialect: str) -> str:
    """Render a physical identifier safely for the selected database dialect."""
    dialect = normalize_sql_dialect(sql_dialect)
    if dialect == "sqlserver":
        return f"[{value.replace(']', ']]')}]"
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        return value
    return f'"{value.replace(chr(34), chr(34) * 2)}"'


def _primary_key(class_name: str) -> str:
    rows = _load_physical_fields().get(class_name, [])
    keys = [row["FieldName"] for row in rows if row["IsPrimaryKey"].lower() == "true"]
    return keys[0] if len(keys) == 1 else ""


def resolve_relationship_join(
    from_class: str,
    to_class: str,
    description: str = "",
) -> dict:
    """Resolve one relationship to an exact physical FK join.

    Relationship descriptions produced by the ontology validator use
    ``CDOName.FieldName``.  The physical CSV then supplies the referenced table
    and field.  A unique FK fallback is supported for older descriptions, but
    ambiguous candidates are never guessed.
    """
    fields_by_class = _load_physical_fields()
    direct = [
        row
        for row in fields_by_class.get(from_class, [])
        if row["IsForeignKey"].lower() == "true"
        and row.get("FKTableName") == to_class
        and row.get("FKFieldName")
    ]
    reverse = [
        row
        for row in fields_by_class.get(to_class, [])
        if row["IsForeignKey"].lower() == "true"
        and row.get("FKTableName") == from_class
        and row.get("FKFieldName")
    ]

    match = re.fullmatch(
        r"([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)",
        description.strip(),
    )
    selected: dict[str, str] | None = None
    direction = ""
    resolution = ""
    if match and match.group(1) == from_class:
        exact = [row for row in direct if row["FieldName"] == match.group(2)]
        if len(exact) == 1:
            selected = exact[0]
            direction = "direct"
            resolution = "relationship_description"
    elif match and match.group(1) == to_class:
        exact = [row for row in reverse if row["FieldName"] == match.group(2)]
        if len(exact) == 1:
            selected = exact[0]
            direction = "reverse"
            resolution = "relationship_description"

    if selected is None and len(direct) == 1:
        selected = direct[0]
        direction = "direct"
        resolution = "unique_physical_fk"
    elif selected is None and len(reverse) == 1:
        selected = reverse[0]
        direction = "reverse"
        resolution = "unique_physical_fk"

    if selected is None:
        return {
            "resolved": False,
            "reason": "ambiguous_or_missing_physical_fk",
            "directCandidates": len(direct),
            "reverseCandidates": len(reverse),
        }

    if direction == "direct":
        source_table = from_class
        source_field = selected["FieldName"]
        target_table = to_class
        target_field = selected["FKFieldName"]
    else:
        source_table = from_class
        source_field = selected["FKFieldName"]
        target_table = to_class
        target_field = selected["FieldName"]

    return {
        "resolved": True,
        "resolution": resolution,
        "direction": direction,
        "sourceTable": source_table,
        "sourceField": source_field,
        "sourcePrimaryKey": _primary_key(source_table),
        "targetTable": target_table,
        "targetField": target_field,
        "targetPrimaryKey": _primary_key(target_table),
        "physicalForeignKeyTable": selected["CDOName"],
        "physicalForeignKeyField": selected["FieldName"],
    }


def build_relationship_sql_section(
    from_class: str,
    rel_name: str,
    to_class: str,
    description: str = "",
    sql_dialect: str = "oracle",
) -> str:
    """Build only the deterministic, read-only query example."""
    dialect = normalize_sql_dialect(sql_dialect)
    dialect_label = "Oracle" if dialect == "oracle" else "SQL Server"
    join = resolve_relationship_join(from_class, to_class, description)
    if not join["resolved"]:
        return "\n".join(
            [
                "> ⚠️ 当前物理 Schema 无法唯一确定该关系的 JOIN 字段，"
                "因此未生成猜测性 SQL。请先核对 `Database_Fields.csv`。",
            ]
        )

    source_table = _sql_identifier(join["sourceTable"], dialect)
    source_field = _sql_identifier(join["sourceField"], dialect)
    target_table = _sql_identifier(join["targetTable"], dialect)
    target_field = _sql_identifier(join["targetField"], dialect)
    table_alias = "" if dialect == "oracle" else " AS"
    parameter = ":SourceId" if dialect == "oracle" else "@SourceId"
    lines = [
        f"### 查询示例（{dialect_label}）",
        "",
        "```sql",
        "SELECT",
        "    src.*,",
        "    tgt.*",
        f"FROM {source_table}{table_alias} src",
        f"LEFT JOIN {target_table}{table_alias} tgt",
        f"    ON src.{source_field} = tgt.{target_field}",
    ]
    if join["sourcePrimaryKey"]:
        lines.append(
            f"WHERE src.{_sql_identifier(join['sourcePrimaryKey'], dialect)} = {parameter};"
        )
    else:
        lines[-1] += ";"
    lines.append("```")
    return "\n".join(lines)


def build_wiki_prefix(
    product_line_name: str,
    from_class: str,
    rel_name: str,
    to_class: str,
    cardinality: str,
    description: str,
    date: str,
    source: str = "物理 Schema + LLM",
) -> str:
    """Build authored Wiki metadata; physical SQL is returned separately."""
    return "\n".join(
        [
            f"# {from_class} → {rel_name} → {to_class}",
            "",
            f"> **产品线**: {product_line_name}",
            f"> **基数**: {cardinality}",
            f"> **生成时间**: {date}",
            f"> **来源**: {source}",
        ]
    )


@lru_cache(maxsize=1)
def _relationship_index() -> dict[tuple[str, str, str], dict]:
    return {
        (
            relationship["fromClass"],
            relationship["relationName"],
            relationship["toClass"],
        ): relationship
        for relationship in collect_all_relationships()
    }


def get_relationship_definition(
    from_class: str,
    rel_name: str,
    to_class: str,
) -> dict | None:
    """Return the canonical ontology relationship used by Wiki fallbacks."""
    return _relationship_index().get((from_class, rel_name, to_class))


def strip_relationship_sql_section(content: str) -> str:
    """Remove the legacy embedded SQL section from an authored Wiki body."""
    if not content or "## SQL 关联示例" not in content:
        return content
    cleaned = re.sub(
        r"(?ms)^## SQL 关联示例[ \t]*\r?\n.*?(?=^## [^\r\n]+|\Z)",
        "",
        content,
        count=1,
    )
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip() + "\n"


def _wiki_has_authored_content(filepath: str, content: str) -> bool:
    """Whether a Wiki contains LLM/user-authored relationship guidance."""
    history = _load_history(filepath.replace(".md", ".meta.json"))
    edits = history.get("edits", [])
    if edits:
        return any(
            edit.get("editor") not in {"physical_schema", ""}
            for edit in edits
        )
    # Legacy authored files may predate companion metadata. The marker below is
    # unique to the physical-only materializer introduced in 2026-07.
    return "物理 Schema 自动生成" not in content


def inject_relationship_sql_section(
    content: str,
    from_class: str,
    rel_name: str,
    to_class: str,
    description: str,
    sql_dialect: str = "oracle",
) -> str:
    """Insert deterministic SQL before the first existing Wiki section."""
    if "## SQL 关联示例" in content:
        return content
    sql_section = build_relationship_sql_section(
        from_class,
        rel_name,
        to_class,
        description,
        sql_dialect=sql_dialect,
    )
    lines = content.splitlines()
    insertion_index = next(
        (
            index
            for index, line in enumerate(lines)
            if line.startswith("## ")
        ),
        len(lines),
    )
    merged = (
        lines[:insertion_index]
        + ["", sql_section, ""]
        + lines[insertion_index:]
    )
    return "\n".join(merged).strip() + "\n"


def build_factual_relationship_wiki(
    product_line: str,
    relationship: dict,
) -> str:
    """Build a physical-fact note without embedding the separately stored SQL."""
    pl_info = get_product_line_info(product_line)
    from_class = relationship["fromClass"]
    rel_name = relationship["relationName"]
    to_class = relationship["toClass"]
    cardinality = relationship.get("cardinality", "")
    description = relationship.get("description", "")
    today = datetime.now().strftime("%Y-%m-%d")
    prefix = build_wiki_prefix(
        pl_info["name"],
        from_class,
        rel_name,
        to_class,
        cardinality,
        description,
        today,
        source="物理 Schema 自动生成",
    )
    facts = [
        "## 关系事实",
        "",
        "本页由本体关系和 `Database_Fields.csv` 自动生成，"
        "不包含未经物理 Schema 验证的业务推断。",
        "",
        f"- 本体关系：`{from_class} --[{rel_name}]--> {to_class}`",
        f"- 基数：`{cardinality or 'UNKNOWN'}`",
        f"- 物理定义：`{description or '—'}`",
    ]
    return f"{prefix}\n\n" + "\n".join(facts) + "\n"


def materialize_factual_relationship_wikis(
    product_line: str = "general",
    upgrade_existing: bool = True,
) -> dict[str, int]:
    """Persist one immediately readable Markdown Wiki per relationship.

    Existing authored Wikis are preserved and legacy embedded SQL is removed.
    Missing Wikis receive a physical-fact marker, but ``read_wiki`` intentionally
    treats it as an empty authored Wiki so the UI can still generate the usage.
    """
    stats = {
        "total": 0,
        "created": 0,
        "upgraded": 0,
        "unchanged": 0,
        "failed": 0,
    }
    for relationship in collect_all_relationships():
        stats["total"] += 1
        from_class = relationship["fromClass"]
        rel_name = relationship["relationName"]
        to_class = relationship["toClass"]
        filepath = _wiki_filepath(
            product_line,
            from_class,
            rel_name,
            to_class,
        )
        try:
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as handle:
                    existing = handle.read()
                if not upgrade_existing:
                    stats["unchanged"] += 1
                    continue
                upgraded = strip_relationship_sql_section(existing)
                if upgraded == existing:
                    stats["unchanged"] += 1
                    continue
                save_wiki(
                    product_line,
                    from_class,
                    rel_name,
                    to_class,
                    upgraded,
                    editor="physical_schema",
                )
                stats["upgraded"] += 1
                continue

            content = build_factual_relationship_wiki(
                product_line,
                relationship,
            )
            save_wiki(
                product_line,
                from_class,
                rel_name,
                to_class,
                content,
                editor="physical_schema",
            )
            stats["created"] += 1
        except Exception as exc:
            print(
                "[WikiManager] Physical Wiki materialization failed for "
                f"{from_class}_{rel_name}_{to_class}: {exc}"
            )
            stats["failed"] += 1
    return stats


WIKI_GENERATE_PROMPT = """你是一个 Siemens Opcenter (Camstar) MES 领域专家。
当前产品线: {product_line_name} ({product_line_desc})

请为以下本体关系(Relationship)生成详细的知识库文档：

关系: {from_class} --[{rel_name}]--> {to_class}
基数: {cardinality}
现有描述: {description}

系统会在独立字段中依据 Database_Fields.csv 展示 SQL 关联示例。
你只生成两个对象之间 relationship 的业务用法，不要重复标题、元数据或 SQL。
直接输出 Markdown，不要包裹在代码块中，并且必须从“## 关系说明”开始：

## 关系说明

（这个关系的含义，在 {product_line_name} 场景中的具体含义，2-3 段）

## 业务场景

### 何时需要配置此关系？
（列出 2-3 个具体的 {product_line_name} 业务场景）

### {product_line_name} 典型示例
（具体的操作示例，包含步骤和参数）

## 配置要点
（5-8 个关键注意事项，条目格式）

## 常见问题 FAQ

**Q: 问题1**
A: 回答1

**Q: 问题2**
A: 回答2

**Q: 问题3**
A: 回答3

---
要求：
- 内容必须结合 {product_line_name} 的实际生产场景
- 如果是"通用 (无产品线)"，则给出通用 Opcenter 建模指导
- 示例要具体可操作
- 全部用中文撰写，技术术语保留英文
- 不要生成、改写或猜测 SQL；SQL 由独立的物理 Schema 字段展示
"""


def generate_wiki_for_relationship(
    product_line: str,
    from_class: str,
    rel_name: str,
    to_class: str,
    cardinality: str = "",
    description: str = "",
    overwrite: bool = False,
) -> dict:
    """
    Use LLM to generate a wiki document for a single relationship.
    Returns: { generated: bool, path: str, content: str }
    """
    # Check if already exists
    filepath = _wiki_filepath(product_line, from_class, rel_name, to_class)
    if os.path.exists(filepath) and not overwrite:
        with open(filepath, "r", encoding="utf-8") as handle:
            existing = handle.read()
        if _wiki_has_authored_content(filepath, existing):
            return {"generated": False, "path": filepath, "reason": "already_exists"}

    pl_info = get_product_line_info(product_line)
    today = datetime.now().strftime("%Y-%m-%d")

    prompt = WIKI_GENERATE_PROMPT.format(
        product_line_name=pl_info["name"],
        product_line_desc=pl_info.get("description", ""),
        from_class=from_class,
        rel_name=rel_name,
        to_class=to_class,
        cardinality=cardinality,
        description=description,
        date=today,
    )
    wiki_prefix = build_wiki_prefix(
        pl_info["name"],
        from_class,
        rel_name,
        to_class,
        cardinality,
        description,
        today,
    )

    try:
        client = _get_llm()
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "你是 Siemens Opcenter MES 领域专家，请根据要求生成高质量的知识库文档。直接输出 Markdown 内容。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=4096,
        )
        body = response.choices[0].message.content.strip()

        # Strip wrapping code blocks if LLM adds them
        if body.startswith("```markdown"):
            body = body[len("```markdown"):].strip()
        elif body.startswith("```md"):
            body = body[len("```md"):].strip()
        elif body.startswith("```"):
            body = body[3:].strip()
        if body.endswith("```"):
            body = body[:-3].strip()
        content = f"{wiki_prefix}\n\n{body}"

        # Save the generated wiki
        save_result = save_wiki(product_line, from_class, rel_name, to_class, content, editor="llm")

        return {"generated": True, "path": filepath, "content": content}

    except Exception as e:
        print(f"[WikiManager] LLM generation failed for {from_class}_{rel_name}_{to_class}: {e}")
        return {"generated": False, "path": filepath, "reason": str(e)}


async def strip_markdown_code_blocks_stream(async_generator):
    """
    Strips leading and trailing markdown code block markers from an async token stream.
    For example, strips leading ```markdown\n, ```md\n, ```\n
    and trailing ``` or similar if they occur.
    """
    buffer = ""
    header_checked = False
    WINDOW_SIZE = 15
    sliding_buffer = ""

    async for chunk in async_generator:
        if not header_checked:
            buffer += chunk
            stripped = buffer.lstrip()
            if not stripped:
                continue
            if stripped.startswith("`"):
                if not stripped.startswith("```"):
                    if len(stripped) < 3:
                        continue
                if "\n" not in stripped:
                    continue
                lines = stripped.split("\n", 1)
                first_line = lines[0].strip()
                if first_line.startswith("```"):
                    buffer = lines[1] if len(lines) > 1 else ""
            else:
                if "\n" not in buffer and len(buffer) < 25:
                    continue
            header_checked = True
            sliding_buffer = buffer
            buffer = ""
            continue
        
        sliding_buffer += chunk
        if len(sliding_buffer) > WINDOW_SIZE:
            yield_len = len(sliding_buffer) - WINDOW_SIZE
            yield sliding_buffer[:yield_len]
            sliding_buffer = sliding_buffer[yield_len:]
            
    if sliding_buffer:
        cleaned = sliding_buffer.rstrip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].rstrip()
        yield cleaned


async def generate_wiki_for_relationship_stream(
    product_line: str,
    from_class: str,
    rel_name: str,
    to_class: str,
    cardinality: str = "",
    description: str = "",
):
    """
    Use AsyncOpenAI to generate a wiki document for a single relationship,
    yielding content chunks progressively and saving it at completion.
    """
    pl_info = get_product_line_info(product_line)
    today = datetime.now().strftime("%Y-%m-%d")

    prompt = WIKI_GENERATE_PROMPT.format(
        product_line_name=pl_info["name"],
        product_line_desc=pl_info.get("description", ""),
        from_class=from_class,
        rel_name=rel_name,
        to_class=to_class,
        cardinality=cardinality,
        description=description,
        date=today,
    )
    wiki_prefix = build_wiki_prefix(
        pl_info["name"],
        from_class,
        rel_name,
        to_class,
        cardinality,
        description,
        today,
    )

    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL, timeout=LLM_TIMEOUT)

    response = await client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "你是 Siemens Opcenter MES 领域专家，请根据要求生成高质量的知识库文档。直接输出 Markdown 内容。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=4096,
        stream=True,
    )

    async def token_generator():
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    clean_generator = strip_markdown_code_blocks_stream(token_generator())

    full_content = f"{wiki_prefix}\n\n"
    yield full_content
    async for token in clean_generator:
        full_content += token
        yield token

    # Save the generated wiki so that it is persisted
    save_wiki(product_line, from_class, rel_name, to_class, full_content.strip(), editor="llm")


def generate_all_wikis(product_line: str, overwrite: bool = False,
                       progress_callback=None) -> dict:
    """
    Batch generate wikis for ALL relationships under a given product line.
    Returns: { total, generated, skipped, failed, details: [...] }
    """
    relationships = collect_all_relationships()
    total = len(relationships)
    generated = 0
    skipped = 0
    failed = 0
    details = []

    for i, rel in enumerate(relationships):
        result = generate_wiki_for_relationship(
            product_line=product_line,
            from_class=rel["fromClass"],
            rel_name=rel["relationName"],
            to_class=rel["toClass"],
            cardinality=rel.get("cardinality", ""),
            description=rel.get("description", ""),
            overwrite=overwrite,
        )

        if result.get("generated"):
            generated += 1
            status = "generated"
        elif result.get("reason") == "already_exists":
            skipped += 1
            status = "skipped"
        else:
            failed += 1
            status = "failed"

        detail = {
            "index": i + 1,
            "total": total,
            "relationship": f"{rel['fromClass']}_{rel['relationName']}_{rel['toClass']}",
            "status": status,
        }
        details.append(detail)

        if progress_callback:
            progress_callback(detail)

        # Rate limiting: small delay between LLM calls
        if result.get("generated"):
            time.sleep(0.5)

    return {
        "product_line": product_line,
        "total": total,
        "generated": generated,
        "skipped": skipped,
        "failed": failed,
        "details": details,
    }


# ══════════════════════════════════════════════════════
#  CLI Entry Point (for manual batch generation)
# ══════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    pl = sys.argv[1] if len(sys.argv) > 1 else "general"
    overwrite = "--overwrite" in sys.argv

    print(f"[WikiManager] Generating wikis for product line: {pl}")
    print(f"[WikiManager] Overwrite: {overwrite}")

    all_rels = collect_all_relationships()
    print(f"[WikiManager] Found {len(all_rels)} relationships")

    def on_progress(detail):
        print(f"  [{detail['index']}/{detail['total']}] {detail['relationship']} → {detail['status']}")

    result = generate_all_wikis(pl, overwrite=overwrite, progress_callback=on_progress)

    print(f"\n[WikiManager] Done! Generated: {result['generated']}, "
          f"Skipped: {result['skipped']}, Failed: {result['failed']}")
