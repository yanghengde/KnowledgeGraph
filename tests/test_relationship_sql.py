from scripts.validate_relationship_sql import audit_relationship_sql
from src.ontology.wiki_manager import read_wiki


def test_history_mainline_container_relationships_render_both_dialects():
    expected_joins = {
        "HAS_BATCH": (
            "src.BatchId = tgt.ContainerId",
            "src.[BatchId] = tgt.[ContainerId]",
        ),
        "HAS_CONTAINER": (
            "src.ContainerId = tgt.ContainerId",
            "src.[ContainerId] = tgt.[ContainerId]",
        ),
    }

    for relationship, (oracle_join, sqlserver_join) in expected_joins.items():
        oracle = read_wiki(
            "general",
            "HistoryMainline",
            relationship,
            "Container",
            sql_dialect="oracle",
        )["sql_content"]
        sqlserver = read_wiki(
            "general",
            "HistoryMainline",
            relationship,
            "Container",
            sql_dialect="sqlserver",
        )["sql_content"]

        assert oracle_join in oracle
        assert oracle.endswith("WHERE src.HistoryMainlineId = :SourceId;\n```")
        assert sqlserver_join in sqlserver
        assert sqlserver.endswith("WHERE src.[HistoryMainlineId] = @SourceId;\n```")


def test_every_relationship_renders_oracle_and_sqlserver_examples():
    report = audit_relationship_sql()

    assert report["relationships"] > 0
    assert report["failures"] == []
    assert report["generatedSqlExamples"] == report["expectedSqlExamples"]
