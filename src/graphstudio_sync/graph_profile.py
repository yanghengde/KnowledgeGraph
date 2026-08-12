"""Business graph profiles and bounded class-level context closure planning."""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable


TRAVERSABLE_STRENGTHS = {"core", "context"}


def _issue(
    severity: str,
    rule: str,
    message: str,
    **details: Any,
) -> dict[str, Any]:
    return {
        "severity": severity,
        "rule": rule,
        "message": message,
        "details": details,
    }


def validate_graph_profile(
    profile: dict[str, Any],
    classes: Iterable[dict[str, Any]],
    relationships: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Validate business intent without guessing missing physical relationships."""

    class_rows = list(classes)
    relationship_rows = list(relationships)
    enabled_classes = {
        row["class_name"]: row for row in class_rows if row.get("enabled", True)
    }
    issues: list[dict[str, Any]] = []
    seeds = [row for row in enabled_classes.values() if row.get("seed_enabled")]
    if not seeds:
        issues.append(_issue("error", "seed.required", "至少需要一个启用的核心种子对象。"))
    for row in seeds:
        if row.get("role") != "core":
            issues.append(
                _issue(
                    "error",
                    "seed.must_be_core",
                    f"{row['class_name']} 被设为种子，但角色不是核心对象。",
                    className=row["class_name"],
                )
            )
    for row in enabled_classes.values():
        if row.get("role") == "core" and row.get("mapping_status") != "resolved":
            issues.append(
                _issue(
                    "error",
                    "core.mapping_unresolved",
                    f"核心对象 {row['class_name']} 尚未解析到物理表。",
                    className=row["class_name"],
                    mappingStatus=row.get("mapping_status"),
                )
            )
        if row.get("review_status") != "approved":
            issues.append(
                _issue(
                    "warning",
                    "class.review_pending",
                    f"对象 {row['class_name']} 的业务角色尚未批准。",
                    className=row["class_name"],
                )
            )
    for row in relationship_rows:
        if not row.get("enabled", True):
            continue
        key = f"{row['source_class']}.{row['relationship_name']}->{row['target_class']}"
        if row.get("traverse") and row.get("strength") not in TRAVERSABLE_STRENGTHS:
            issues.append(
                _issue(
                    "error",
                    "relationship.unsafe_traversal",
                    f"关系 {key} 为弱关联/按需关联，不能驱动上下文扩展。",
                    relationship=key,
                )
            )
        if row.get("traverse") and (
            row["source_class"] not in enabled_classes
            or row["target_class"] not in enabled_classes
        ):
            issues.append(
                _issue(
                    "error",
                    "relationship.class_not_enabled",
                    f"关系 {key} 的两端必须先加入并启用业务图谱。",
                    relationship=key,
                )
            )
        if row.get("required_context") and row.get("mapping_status") != "resolved":
            issues.append(
                _issue(
                    "error",
                    "relationship.required_mapping_unresolved",
                    f"必需上下文关系 {key} 没有唯一、可执行的物理映射。",
                    relationship=key,
                    mappingStatus=row.get("mapping_status"),
                )
            )
        elif row.get("traverse") and row.get("mapping_status") != "resolved":
            issues.append(
                _issue(
                    "warning",
                    "relationship.mapping_unresolved",
                    f"关系 {key} 尚不可执行，不会进入数据闭包。",
                    relationship=key,
                    mappingStatus=row.get("mapping_status"),
                )
            )
        if row.get("review_status") != "approved":
            issues.append(
                _issue(
                    "warning",
                    "relationship.review_pending",
                    f"关系 {key} 的业务强度尚未批准。",
                    relationship=key,
                )
            )
    if int(profile.get("max_depth") or 0) > 4:
        issues.append(
            _issue(
                "warning",
                "profile.depth_high",
                "上下文深度大于 4，可能导致关系扇出快速放大。",
                maxDepth=profile.get("max_depth"),
            )
        )
    return issues


def plan_context_closure(
    profile: dict[str, Any],
    classes: Iterable[dict[str, Any]],
    relationships: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Build a safe class-level expansion plan; this function never reads source rows."""

    class_rows = list(classes)
    relationship_rows = list(relationships)
    class_by_name = {
        row["class_name"]: row
        for row in class_rows
        if row.get("enabled", True) and row.get("role") != "excluded"
    }
    seeds = sorted(
        (
            row["class_name"]
            for row in class_by_name.values()
            if row.get("seed_enabled") and row.get("role") == "core"
        ),
        key=lambda name: (int(class_by_name[name].get("priority") or 100), name),
    )
    max_depth = int(profile.get("max_depth") or 0)
    visited = set(seeds)
    frontier = set(seeds)
    steps: list[dict[str, Any]] = []

    executable = [
        row
        for row in relationship_rows
        if row.get("enabled", True)
        and row.get("traverse")
        and row.get("strength") in TRAVERSABLE_STRENGTHS
        and row.get("mapping_status") == "resolved"
    ]
    for depth in range(1, max_depth + 1):
        next_frontier: set[str] = set()
        for edge in executable:
            edge_max_depth = edge.get("max_depth")
            if edge_max_depth is not None and depth > int(edge_max_depth):
                continue
            source = edge["source_class"]
            target = edge["target_class"]
            directions: list[tuple[str, str, str]] = []
            if edge.get("direction", "outgoing") in {"outgoing", "both"}:
                directions.append((source, target, "outgoing"))
            if edge.get("direction") in {"incoming", "both"}:
                directions.append((target, source, "incoming"))
            for from_class, to_class, direction in directions:
                if from_class not in frontier or to_class not in class_by_name:
                    continue
                steps.append(
                    {
                        "depth": depth,
                        "fromClass": from_class,
                        "relationship": edge["relationship_name"],
                        "toClass": to_class,
                        "direction": direction,
                        "strength": edge["strength"],
                        "requiredContext": bool(edge.get("required_context")),
                        "maxTargetsPerSource": int(edge.get("max_targets_per_source") or 50),
                    }
                )
                if to_class not in visited:
                    next_frontier.add(to_class)
        if not next_frontier:
            break
        visited.update(next_frontier)
        frontier = next_frontier

    included = sorted(
        (class_by_name[name] for name in visited),
        key=lambda row: (
            {"core": 0, "context": 1, "reference": 2, "on_demand": 3}.get(row["role"], 9),
            int(row.get("priority") or 100),
            row["class_name"],
        ),
    )
    role_counts = Counter(row["role"] for row in included)
    estimated_nodes = 0
    for row in included:
        rows = int(row.get("approximate_rows") or 0)
        per_class_limit = row.get("max_instances_per_run")
        estimated_nodes += min(rows, int(per_class_limit)) if per_class_limit else rows
    global_limit = int(profile.get("max_total_nodes_per_run") or 0)
    issues = validate_graph_profile(profile, class_rows, relationship_rows)
    if global_limit and estimated_nodes > global_limit:
        issues.append(
            _issue(
                "warning",
                "profile.node_budget_exceeded",
                "按源表估算的实例数超过单次运行预算，执行器必须分批并在预算处停止。",
                estimatedNodes=estimated_nodes,
                maxTotalNodesPerRun=global_limit,
            )
        )
    severity_counts = Counter(issue["severity"] for issue in issues)
    return {
        "profileKey": profile.get("profile_key"),
        "previewOnly": True,
        "sourceRowsRead": False,
        "graphStudioMutated": False,
        "seeds": seeds,
        "includedClasses": [
            {
                "className": row["class_name"],
                "role": row["role"],
                "orphanPolicy": row["orphan_policy"],
                "approximateRows": int(row.get("approximate_rows") or 0),
                "maxInstancesPerRun": row.get("max_instances_per_run"),
            }
            for row in included
        ],
        "steps": steps,
        "limits": {
            "maxDepth": max_depth,
            "maxContextNodesPerSeed": int(profile.get("max_context_nodes_per_seed") or 0),
            "maxTotalNodesPerRun": global_limit,
        },
        "summary": {
            "includedClassCount": len(included),
            "traversalStepCount": len(steps),
            "estimatedNodesBeforeBudget": estimated_nodes,
            "roleCounts": dict(role_counts),
            "errors": severity_counts["error"],
            "warnings": severity_counts["warning"],
        },
        "issues": issues,
    }
