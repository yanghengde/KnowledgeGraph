"""Conservative, schema-bound capabilities for everyday manufacturing questions.

Aliases route language only. Every URI, field and edge is resolved from the
published schema; unsupported filters and ambiguous joins fall through to the
dynamic planner instead of silently returning an unfiltered answer.
"""

from dataclasses import dataclass
from collections import deque
import html
import re
from typing import Any

from rdflib import Literal


ALIASES = {
    "MfgOrder": ("制造订单", "生产订单", "生产工单", "工单", "订单"),
    "Product": ("产品",), "Container": ("批次", "容器"),
    "Workflow": ("工作流", "工艺流程"), "WorkflowStep": ("流程步骤", "工作流步骤"),
    "Spec": ("工艺规范", "工序规范"), "Operation": ("工序", "作业"),
    "Resource": ("设备", "资源"), "Employee": ("员工", "人员"),
    "Material": ("物料",), "Factory": ("工厂",),
}


def local(uri: str) -> str:
    return uri.rsplit("#", 1)[-1].rsplit("/", 1)[-1]


def iri(value: str) -> str:
    if not value.startswith(("https://", "http://", "urn:")) or re.search(r'[<>\s"{}\\]', value):
        raise ValueError("Invalid published schema URI")
    return f"<{value}>"


def class_names(rows):
    classes = {}
    for row in rows:
        uri = row.get("class")
        if uri:
            classes.setdefault(uri, row.get("classLabel") or local(uri))
    return classes


def aliases(uri, label):
    return tuple(dict.fromkeys((*ALIASES.get(local(uri), ()), label, local(uri))))


@dataclass(frozen=True)
class QueryCapability:
    key: str
    title: str
    sparql: str
    columns: dict[str, str]
    parameters: dict[str, Any]


def match_capability(question, rows, runtime, history=None):
    text = re.sub(r"[\s，。？！?！,]", "", question)
    # Elliptical questions must retain the previous filters in the LLM route.
    if re.search(r"这些|它们|上述|刚才|其中|继续|前面|只看|除了|不含|最近|今天|昨天|本月", text):
        return None
    previous = next((m.get("content", "") for m in reversed(history or []) if m.get("role") == "user"), "")
    if previous and re.search(r"\d|筛选|仅|只|工厂|今天|昨天|本月", previous) and not text.startswith(("当前发布", "全部", "所有")):
        return None
    names = class_names(rows)
    alias_pairs = [(a, uri) for uri, label in names.items() for a in aliases(uri, label)]
    alias_pairs.sort(key=lambda item: -len(item[0]))
    bindings = {}
    for alias, uri in alias_pairs:
        # A shared business alias is ambiguous; do not pick one arbitrarily.
        bindings.setdefault(alias, set()).add(uri)
    unique = {alias: next(iter(uris)) for alias, uris in bindings.items() if len(uris) == 1}
    if not unique:
        return None
    pattern = "|".join(re.escape(a) for a in sorted(unique, key=len, reverse=True))
    text = re.sub(pattern, lambda m: "{" + unique[m.group()] + "}", text)
    tokens = re.findall(r"\{([^{}]+)\}", text)
    if not tokens or len(set(tokens)) > 2:
        return None
    # Replace the long URI tokens before interpreting the small grammar.
    source = tokens[0]
    target = tokens[1] if len(tokens) > 1 else None
    normalized = text.replace("{" + source + "}", "A")
    if target:
        normalized = normalized.replace("{" + target + "}", "B")
    prefix = r"(?:请|帮我|查询|列出|查看)*(?:当前(?:发布(?:的|了)?)?|已发布的|全部|所有)?"
    kind = None
    code = None
    if re.fullmatch(prefix + r"(?:有?哪些A|A(?:有哪些|列表|清单|是哪些|都有哪些))", normalized):
        kind = "list"
    elif re.fullmatch(prefix + r"(?:有多少(?:个|条)?A|A(?:有多少(?:个|条)?|数量|总数))", normalized):
        kind = "count"
    elif target and re.fullmatch(prefix + r"(?:每个|每条|各个)?A(?:分别)?(?:对应|关联|关联了|对应的|关联的)(?:的)?(?:什么|哪些)?B(?:是什么|是哪些|有哪些)?", normalized):
        kind = "link"
    elif target and re.fullmatch(r"按A统计(?:关联的)?B(?:数量|个数)", normalized):
        kind = "group"
        source, target = target, source
    elif local(source) == "MfgOrder" and target:
        match = re.fullmatch(r"A(MO-[A-Za-z0-9-]+)(?:对应|关联|对应的|关联的)(?:的)?B(?:是什么|有哪些)?", normalized)
        if match:
            kind, code = "link", match.group(1)
    if kind is None:
        return None
    layer = iri(runtime["layerUri"])
    a = iri(source)
    source_title = ALIASES.get(local(source), (names[source],))[0]
    properties = {r.get("property") for r in rows if r.get("class") == source and r.get("valueKind") == "属性"}
    name_property = next((p for p in properties if p and local(p) == local(source) + "_name"), None)
    def label_pattern(uri, var, out):
        props = [r.get("property") for r in rows if r.get("class") == uri and r.get("valueKind") == "属性"]
        prop = next((p for p in props if p and local(p) == local(uri) + "_displayLabel"), None)
        prop = prop or next((p for p in props if p and local(p) == local(uri) + "_name"), None)
        if prop:
            return f"OPTIONAL {{ ?{var} {iri(prop)} ?{out}Value }} BIND(COALESCE(?{out}Value, STR(?{var})) AS ?{out})"
        return f"BIND(STR(?{var}) AS ?{out})"
    conditions = f"?object a {a} . "
    parameters = {"limit": 100}
    if code:
        if not name_property:
            return None
        conditions += f"?object {iri(name_property)} {Literal(code).n3()} . "
        parameters["orderName"] = code
    if kind == "count":
        query = f"SELECT (COUNT(DISTINCT ?object) AS ?count) WHERE {{ GRAPH {layer} {{ {conditions} }} }} LIMIT 1"
        return QueryCapability("count", f"{source_title}数量", query, {"count": f"{source_title}数量"}, parameters)
    source_label = label_pattern(source, "object", "name")
    if kind == "list":
        query = f"SELECT DISTINCT ?object ?name WHERE {{ GRAPH {layer} {{ {conditions} {source_label} }} }} ORDER BY ?name ?object LIMIT 100"
        return QueryCapability("list", f"{source_title}清单", query, {"name": source_title, "object": "对象标识"}, parameters)
    links = {(r["property"], r["class"] == source) for r in rows
             if r.get("valueKind") == "关系" and r.get("questionEnabled", True) is not False
             and (r.get("relationshipCount") is None or int(r["relationshipCount"]) > 0)
             and ((r.get("class") == source and r.get("targetClass") == target)
                  or (r.get("class") == target and r.get("targetClass") == source))}
    if len(links) != 1:
        return None
    predicate, forward = next(iter(links))
    edge = f"?object {iri(predicate)} ?related ." if forward else f"?related {iri(predicate)} ?object ."
    target_label = label_pattern(target, "related", "relatedName")
    target_title = ALIASES.get(local(target), (names.get(target, local(target)),))[0]
    if kind == "group":
        query = f"SELECT ?related ?relatedName (COUNT(DISTINCT ?object) AS ?count) WHERE {{ GRAPH {layer} {{ {conditions} {edge} ?related a {iri(target)} . {target_label} }} }} GROUP BY ?related ?relatedName ORDER BY DESC(?count) ?related LIMIT 100"
        columns = {"relatedName": target_title, "count": f"{source_title}数量", "related": "关联对象标识"}
    else:
        query = f"SELECT DISTINCT ?object ?name ?related ?relatedName WHERE {{ GRAPH {layer} {{ {conditions} {source_label} OPTIONAL {{ {edge} ?related a {iri(target)} . {target_label} }} }} }} ORDER BY ?name ?object ?related LIMIT 100"
        columns = {"name": source_title, "relatedName": target_title, "object": "对象标识", "related": "关联对象标识"}
    return QueryCapability(kind, f"{source_title}与{target_title}" if kind == "link" else f"按{target_title}统计{source_title}", query, columns, parameters)


def retrieve_schema(question, rows, history=None, max_classes=8, max_properties=16):
    """Lexical ontology retrieval with bounded path expansion, never data search."""
    names = class_names(rows)
    text = question.casefold()
    contextual = bool(re.search(r"这些|它们|上述|其中|对应|关联|呢", question))
    if contextual or not any(a.casefold() in text for u, l in names.items() for a in aliases(u, l)):
        text += " " + next((m.get("content", "") for m in reversed(history or []) if m.get("role") == "user"), "").casefold()
    scores = {u: max((len(a) for a in aliases(u, l) if a and a.casefold() in text), default=0) for u, l in names.items()}
    # Property names/labels can identify a class even without an object alias.
    for row in rows:
        label = str(row.get("propertyLabel") or "")
        if len(label) > 2 and label.casefold() in text:
            scores[row["class"]] = scores.get(row["class"], 0) + 1
    seeds = sorted((u for u in names if scores[u]), key=lambda u: (-scores[u], u))[:max_classes]
    if not seeds:
        return []
    selected = set(seeds)
    adjacency = {}
    for row in rows:
        if row.get("valueKind") == "关系" and row.get("questionEnabled", True) is not False:
            a, b = row["class"], row.get("targetClass")
            if b in names:
                adjacency.setdefault(a, set()).add(b)
                adjacency.setdefault(b, set()).add(a)
    # Connect mentioned classes through short ontology paths.
    for start in seeds:
        for end in seeds:
            queue = deque([(start, [start])]); seen = {start}
            while queue:
                node, path = queue.popleft()
                if node == end:
                    if len(selected | set(path)) <= max_classes:
                        selected.update(path)
                    break
                if len(path) <= 3:
                    for nxt in sorted(adjacency.get(node, set()) - seen):
                        seen.add(nxt); queue.append((nxt, path + [nxt]))
    if len(seeds) == 1:
        selected.update(sorted(adjacency.get(seeds[0], set()))[:max_classes - 1])
    result = []
    for uri in sorted(selected):
        own = [r for r in rows if r.get("class") == uri]
        result.extend(r for r in own if not r.get("property"))
        result.extend(r for r in own if r.get("valueKind") == "关系" and r.get("targetClass") in selected)
        props = [r for r in own if r.get("valueKind") == "属性"]
        def rank(row):
            label = str(row.get("propertyLabel") or local(row.get("property", ""))).casefold()
            simple = local(row.get("property", "")).removeprefix(local(uri) + "_").casefold()
            return (0 if label and label in text else 1 if simple in {"name", "displaylabel", "description", "qty", "status", "orderstatus"} else 2, simple)
        result.extend(sorted(props, key=rank)[:max_properties])
    return result


def result_table(rows, variables, columns=None):
    """Render factual rows immediately; never turn a cell into HTML/Markdown."""
    def cell(value):
        value = html.escape(str("—" if value is None or value == "" else value), quote=False)
        return re.sub(r"([\\`*_\[\]{}|])", r"\\\1", value).replace("\r", " ").replace("\n", " ")
    if not rows:
        return "当前发布版本中未找到符合本次查询条件的记录。\n"
    shown = list(columns) if columns else list(variables)[:12]
    # Keep stable object identifiers in evidence, hide them only when every
    # displayed name identifies a single URI in this result set.
    for identifier, label in (("object", "name"), ("related", "relatedName")):
        mapping = {}
        for row in rows:
            mapping.setdefault(row.get(label, ""), set()).add(row.get(identifier, ""))
        if identifier in shown and label in shown and all(len(v) == 1 for v in mapping.values()):
            shown.remove(identifier)
    titles = columns or {}
    lines = ["| " + " | ".join(cell(titles.get(v, v)) for v in shown) + " |",
             "| " + " | ".join("---" for _ in shown) + " |"]
    lines += ["| " + " | ".join(cell(row.get(v, "")) for v in shown) + " |" for row in rows[:100]]
    note = "本次最多展示 100 条，可能还有更多结果，请增加筛选条件。" if len(rows) >= 100 else f"本次查询返回 {len(rows)} 条记录。"
    return note + "\n\n" + "\n".join(lines) + "\n\n空白项表示本次查询未返回该值。\n"
