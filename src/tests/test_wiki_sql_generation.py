from src.ontology.wiki_manager import (
    build_factual_relationship_wiki,
    build_relationship_sql_section,
    build_wiki_prefix,
    collect_all_relationships,
    get_wiki_stats,
    materialize_factual_relationship_wikis,
    read_wiki,
    resolve_relationship_join,
    strip_relationship_sql_section,
)


def test_master_recipe_printer_label_join_uses_physical_fk():
    join = resolve_relationship_join(
        "MasterRecipe",
        "PrinterLabelDefinition",
        "MasterRecipe.PrinterLabelDefinitionId",
    )

    assert join["resolved"] is True
    assert join["sourceField"] == "PrinterLabelDefinitionId"
    assert join["targetField"] == "PrinterLabelDefinitionId"
    assert join["sourcePrimaryKey"] == "MasterRecipeId"

    section = build_relationship_sql_section(
        "MasterRecipe",
        "HAS_PRINTER_LABEL_DEFINITION",
        "PrinterLabelDefinition",
        "MasterRecipe.PrinterLabelDefinitionId",
        sql_dialect="sqlserver",
    )
    assert "FROM [MasterRecipe] AS src" in section
    assert "LEFT JOIN [PrinterLabelDefinition] AS tgt" in section
    assert (
        "ON src.[PrinterLabelDefinitionId] = "
        "tgt.[PrinterLabelDefinitionId]"
    ) in section
    assert "WHERE src.[MasterRecipeId] = @SourceId" in section
    assert section.startswith("### 查询示例")
    assert "物理关联" not in section
    assert "源表：" not in section
    assert "LEFT JOIN` 会保留" not in section


def test_oracle_relationship_sql_uses_oracle_aliases_and_parameters():
    section = build_relationship_sql_section(
        "MasterRecipe",
        "HAS_PRINTER_LABEL_DEFINITION",
        "PrinterLabelDefinition",
        "MasterRecipe.PrinterLabelDefinitionId",
        sql_dialect="oracle",
    )

    assert section.startswith("### 查询示例（Oracle）")
    assert "FROM MasterRecipe src" in section
    assert "LEFT JOIN PrinterLabelDefinition tgt" in section
    assert (
        "ON src.PrinterLabelDefinitionId = "
        "tgt.PrinterLabelDefinitionId"
    ) in section
    assert "WHERE src.MasterRecipeId = :SourceId" in section
    assert "[" not in section
    assert "@SourceId" not in section
    assert " AS src" not in section


def test_authored_wiki_prefix_does_not_embed_sql():
    prefix = build_wiki_prefix(
        "通用",
        "MasterRecipe",
        "HAS_PRINTER_LABEL_DEFINITION",
        "PrinterLabelDefinition",
        "MANY_TO_ONE",
        "MasterRecipe.PrinterLabelDefinitionId",
        "2026-07-28",
    )

    assert prefix.startswith(
        "# MasterRecipe → HAS_PRINTER_LABEL_DEFINITION → "
        "PrinterLabelDefinition"
    )
    assert "## SQL 关联示例" not in prefix
    assert "## 关系说明" not in prefix


def test_every_current_relationship_resolves_to_one_physical_join():
    unresolved = []
    for relationship in collect_all_relationships():
        join = resolve_relationship_join(
            relationship["fromClass"],
            relationship["toClass"],
            relationship.get("description", ""),
        )
        if not join["resolved"]:
            unresolved.append(
                (
                    relationship["fromClass"],
                    relationship["relationName"],
                    relationship["toClass"],
                )
            )

    assert unresolved == []


def test_every_relationship_exposes_sql_in_its_own_field():
    unavailable_sql = []
    for relationship in collect_all_relationships():
        for sql_dialect in ("oracle", "sqlserver"):
            result = read_wiki(
                "general",
                relationship["fromClass"],
                relationship["relationName"],
                relationship["toClass"],
                sql_dialect=sql_dialect,
            )
            sql_content = result["sql_content"]
            syntax_is_valid = (
                "### 查询示例" in sql_content
                and (
                    (
                        sql_dialect == "oracle"
                        and "### 查询示例（Oracle）" in sql_content
                        and "[" not in sql_content
                        and "@SourceId" not in sql_content
                        and " AS src" not in sql_content
                    )
                    or (
                        sql_dialect == "sqlserver"
                        and "### 查询示例（SQL Server）" in sql_content
                        and "FROM [" in sql_content
                        and " AS src" in sql_content
                    )
                )
            )
            if not syntax_is_valid:
                unavailable_sql.append(
                    (
                        sql_dialect,
                        relationship["fromClass"],
                        relationship["relationName"],
                        relationship["toClass"],
                    )
                )

    assert unavailable_sql == []


def test_factual_fallback_has_no_unverified_business_claims():
    relationship = {
        "fromClass": "MasterRecipe",
        "relationName": "HAS_PRINTER_LABEL_DEFINITION",
        "toClass": "PrinterLabelDefinition",
        "cardinality": "MANY_TO_ONE",
        "description": "MasterRecipe.PrinterLabelDefinitionId",
    }
    content = build_factual_relationship_wiki("general", relationship)

    assert "物理 Schema 自动生成" in content
    assert "不包含未经物理 Schema 验证的业务推断" in content
    assert "## SQL 关联示例" not in content


def test_legacy_embedded_sql_is_removed_from_authored_content():
    legacy = """# A → HAS_B → B

> **来源**: 物理 Schema + LLM

## SQL 关联示例

```sql
SELECT 1;
```

## 关系说明

这里是 relationship 的业务用法。
"""
    content = strip_relationship_sql_section(legacy)

    assert "SQL 关联示例" not in content
    assert "SELECT 1" not in content
    assert "## 关系说明" in content


def test_physical_only_wiki_keeps_usage_empty_but_sql_available():
    result = read_wiki(
        "general",
        "Workflow",
        "HAS_ERP_ROUTE",
        "ERPRoute",
        sql_dialect="sqlserver",
    )

    assert result["found"] is False
    assert result["content"] == ""
    assert "FROM [Workflow] AS src" in result["sql_content"]


def test_authored_wiki_keeps_usage_and_hides_embedded_sql():
    result = read_wiki(
        "general",
        "HistoryMainline",
        "HAS_WORKFLOW_STEP",
        "WorkflowStep",
    )

    assert result["found"] is True
    assert "## 关系说明" in result["content"]
    assert "## SQL 关联示例" not in result["content"]
    assert "### 查询示例" in result["sql_content"]


def test_wiki_stats_include_factual_fallback_coverage():
    stats = get_wiki_stats("general")["product_lines"]["general"]

    assert stats["available_count"] == stats["total_relationships"]
    assert stats["coverage"] == 100.0


def test_materializer_api_is_available():
    assert callable(materialize_factual_relationship_wikis)
