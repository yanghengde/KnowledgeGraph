from src.graphstudio_sync.graph_profile import plan_context_closure, validate_graph_profile


def _profile(**overrides):
    return {
        "profile_key": "opcenter2607-core",
        "max_depth": 2,
        "max_context_nodes_per_seed": 200,
        "max_total_nodes_per_run": 1000,
        **overrides,
    }


def _class(name, role, *, seed=False, rows=10, review="approved"):
    return {
        "class_name": name,
        "role": role,
        "orphan_policy": "quarantine",
        "seed_enabled": seed,
        "enabled": True,
        "review_status": review,
        "mapping_status": "resolved",
        "approximate_rows": rows,
        "priority": 10,
    }


def _relationship(source, name, target, *, strength="context", traverse=True, status="resolved"):
    return {
        "source_class": source,
        "relationship_name": name,
        "target_class": target,
        "strength": strength,
        "required_context": False,
        "traverse": traverse,
        "direction": "outgoing",
        "max_depth": None,
        "max_targets_per_source": 50,
        "enabled": True,
        "review_status": "approved",
        "mapping_status": status,
    }


def test_context_closure_only_follows_approved_executable_relationships() -> None:
    classes = [
        _class("MfgOrder", "core", seed=True),
        _class("Product", "core"),
        _class("Operation", "context"),
        _class("AuditLog", "context"),
    ]
    relationships = [
        _relationship("MfgOrder", "USES_PRODUCT", "Product", strength="core"),
        _relationship("Product", "USES_OPERATION", "Operation"),
        _relationship("MfgOrder", "HAS_AUDIT", "AuditLog", strength="weak", traverse=False),
    ]

    plan = plan_context_closure(_profile(), classes, relationships)

    assert plan["seeds"] == ["MfgOrder"]
    assert [item["className"] for item in plan["includedClasses"]] == [
        "MfgOrder", "Product", "Operation"
    ]
    assert plan["summary"]["traversalStepCount"] == 2
    assert plan["sourceRowsRead"] is False
    assert plan["graphStudioMutated"] is False


def test_unresolved_relationship_is_not_executable_and_is_reported() -> None:
    classes = [_class("MfgOrder", "core", seed=True), _class("Product", "context")]
    relationships = [
        _relationship("MfgOrder", "USES_PRODUCT", "Product", status="ambiguous")
    ]

    plan = plan_context_closure(_profile(), classes, relationships)

    assert [item["className"] for item in plan["includedClasses"]] == ["MfgOrder"]
    assert plan["summary"]["traversalStepCount"] == 0
    assert any(item["rule"] == "relationship.mapping_unresolved" for item in plan["issues"])


def test_weak_relationship_cannot_drive_context_expansion() -> None:
    classes = [_class("MfgOrder", "core", seed=True), _class("AuditLog", "context")]
    relationships = [
        _relationship("MfgOrder", "HAS_AUDIT", "AuditLog", strength="weak", traverse=True)
    ]

    issues = validate_graph_profile(_profile(), classes, relationships)

    assert any(item["rule"] == "relationship.unsafe_traversal" for item in issues)


def test_node_budget_warning_is_generated_without_reading_rows() -> None:
    classes = [_class("MfgOrder", "core", seed=True, rows=5000)]

    plan = plan_context_closure(_profile(max_total_nodes_per_run=100), classes, [])

    assert plan["summary"]["estimatedNodesBeforeBudget"] == 5000
    assert any(item["rule"] == "profile.node_budget_exceeded" for item in plan["issues"])
