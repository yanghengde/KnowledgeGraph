"""Review local ontology definitions without requiring the modeling database."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from src.ontology import authority as catalog
from src.ontology.authority_store import authority_store

router = APIRouter(prefix="/api/ontology-authority", tags=["Ontology authority"])


class Decision(BaseModel):
    preferredSource: str = Field(max_length=200)
    choices: dict[str, str] = Field(default_factory=dict)
    domain: str = Field(min_length=1, max_length=80)
    fingerprint: str = Field(min_length=64, max_length=64)
    planHash: str | None = None
    chineseName: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=16000)


class Revision(BaseModel):
    revision: int = Field(gt=0)


def _store():
    try:
        return authority_store()
    except Exception as exc:
        raise HTTPException(503, "本体治理控制面暂不可用，请检查 PostgreSQL 连接") from exc


def _documents():
    from src.graphstudio_sync.ontology_backend import backend
    documents = catalog.read_library()
    if backend() == "postgres":
        from web.ontology_postgres_view import documents as postgres_documents
        documents.update(postgres_documents())
    return documents


def _detail(name, conn=None):
    authorities, proposals = _store().snapshot(conn)
    try:
        return catalog.class_detail(name, _documents(), authorities.get(name), proposals)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.get("")
def directory():
    authorities, proposals = _store().snapshot()
    return catalog.directory(_documents(), authorities, proposals)


@router.get("/classes/{name}")
def detail(name: str):
    value = _detail(name)
    value.pop("physical")
    value["history"] = _store().history(name)
    return value


def _plan(name, request, conn=None):
    current = _detail(name, conn)
    if request.fingerprint != current["fingerprint"]:
        raise HTTPException(409, "模型来源或版本已变化，请刷新后重新审阅")
    try:
        return catalog.merge_plan(current, request.preferredSource, request.choices, request.domain, request.chineseName, request.description)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/classes/{name}/preview")
def preview(name: str, request: Decision):
    return _plan(name, request)


@router.post("/classes/{name}/approve")
def approve(name: str, request: Decision):
    store = _store()
    with store.engine.begin() as conn:
        conn.execute(text("SELECT pg_advisory_xact_lock(721603051)"))
        plan = _plan(name, request, conn)
        if not request.planHash or plan["planHash"] != request.planHash:
            raise HTTPException(409, "请先预览本次差异，再确认相同的合并结果")
        if plan["blockers"]:
            raise HTTPException(422, "；".join(plan["blockers"]))
        return store.save(conn, plan)


@router.post("/classes/{name}/sync")
def sync(name: str, request: Revision):
    store = _store()
    with store.engine.begin() as conn:
        conn.execute(text("SELECT pg_advisory_xact_lock(721603051)"))
        authorities, _ = store.snapshot(conn)
        record = authorities.get(name)
        if not record or record["revision"] != request.revision:
            raise HTTPException(409, "权威版本已变化，请刷新后同步")
        from src.graphstudio_sync.ontology_backend import backend
        if backend() == "postgres":
            from src.graphstudio_sync.ontology_store import source_payload, save_source
            conn.execute(text("SELECT pg_advisory_xact_lock(721603061)"))
            payload = source_payload(None, conn)
            cls = record["model"]["class"]
            known = {c["name"] for c in payload["classes"]} | {name}
            relations = record["model"]["relationships"]
            if any(r["toClass"] not in known for r in relations):
                raise HTTPException(422, "请先导入关系终点的 CSV 模型")
            payload["classes"] = [c for c in payload["classes"] if c["name"] != name] + [{"name": name,
                "chineseName": cls.get("chineseName", ""), "description": cls.get("description", ""), "module": record["domain"], "layer": "Config", "authorityRevision": request.revision}]
            payload["properties"] = [p for p in payload["properties"] if p["className"] != name] + [{**p, "className": name, "dataType": p.get("type", "String")} for p in cls.get("properties", [])]
            payload["relationships"] = [r for r in payload["relationships"] if r["source"] != name] + [{**r, "source": name, "target": r["toClass"], "name": r["relationName"]} for r in relations]
            for key, order in (("classes", lambda c:c["name"]), ("properties", lambda p:(p["className"],p["name"])), ("relationships", lambda r:(r["source"],r["name"],r["target"]))):
                payload[key].sort(key=order)
            save_source(conn, payload, {"kind": "authority", "className": name, "revision": request.revision}, activate=True)
            conn.execute(text("UPDATE graphsync.ontology_authority SET synced_revision=:revision WHERE class_name=:name"), {"revision": request.revision,"name": name})
        else:
            from web.shared import driver
            cls = record["model"]["class"]
            relationships = record["model"]["relationships"]
            def write(tx):
                targets = sorted({r["toClass"] for r in relationships if r["toClass"] != name})
                found = {r["name"] for r in tx.run("MATCH (c:OntologyClass) WHERE c.name IN $names RETURN c.name AS name", names=targets)}
                missing = sorted(set(targets) - found)
                if missing:
                    raise ValueError("请先同步关系终点：" + "、".join(missing[:15]))
                tx.run("""MERGE (c:OntologyClass {name:$name}) SET c.chineseName=$label,
                    c.description=$description,c.module=$domain,c.authorityRevision=$revision,c.layer='Config'""",
                    name=name,label=cls.get("chineseName", ""),description=cls.get("description", ""),domain=record["domain"],revision=request.revision).consume()
                tx.run("""UNWIND $properties AS p MATCH (c:OntologyClass {name:$name})
                    MERGE (a:OntologyProperty {className:$name,name:p.name})
                    SET a.dataType=coalesce(p.type,'String'),a.description=coalesce(p.description,''),a.required=coalesce(p.required,false)
                    MERGE (c)-[:HAS_PROPERTY]->(a)""",name=name,properties=cls.get("properties", [])).consume()
                tx.run("""UNWIND $relations AS r MATCH (s:OntologyClass {name:$name}),(t:OntologyClass {name:r.toClass})
                    MERGE (s)-[e:ONTOLOGY_RELATION {name:r.relationName}]->(t)
                    SET e.description=coalesce(r.description,''),e.cardinality=coalesce(r.cardinality,'UNKNOWN')""",name=name,relations=relationships).consume()
            try:
                with driver.session() as session:
                    session.execute_write(write)
            except ValueError as exc:
                raise HTTPException(422, str(exc)) from exc
            except Exception as exc:
                raise HTTPException(503, "建模库同步未完成，权威版本已保存；检查 Neo4j 连接后可安全重试") from exc
            conn.execute(text("UPDATE graphsync.ontology_authority SET synced_revision=:revision WHERE class_name=:name"), {"revision": request.revision,"name": name})
    from web.routers.ontology_import import _invalidate_graph_caches
    _invalidate_graph_caches()
    return {"status": "synced", "revision": request.revision}
