import json
from typing import Literal
from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

router = APIRouter()

class WikiSaveRequest(BaseModel):
    source: str
    rel: str
    target: str
    product_line: str = "general"
    content: str
    editor: str = "user"


class WikiGenerateOneRequest(BaseModel):
    source: str
    rel: str
    target: str
    product_line: str = "general"
    cardinality: str = ""
    description: str = ""
    overwrite: bool = False


class WikiGenerateBatchRequest(BaseModel):
    product_line: str = "general"
    overwrite: bool = False


@router.get("/api/wiki/relationship")
def get_wiki_relationship(
    source: str,
    rel: str,
    target: str,
    product_line: str = "general",
    sql_dialect: Literal["oracle", "sqlserver"] = "oracle",
):
    from src.ontology.wiki_manager import read_wiki
    result = read_wiki(
        product_line,
        source,
        rel,
        target,
        sql_dialect=sql_dialect,
    )
    return JSONResponse(
        content={
            "found": result["found"],
            "product_line": result.get("product_line", product_line),
            "content": result.get("content", ""),
            "sql_content": result.get("sql_content", ""),
            "metadata": result.get("metadata", {}),
            "reason": result.get("reason", ""),
            "sql_dialect": sql_dialect,
        },
        headers={"Cache-Control": "no-store"},
    )


@router.post("/api/wiki/save")
def save_wiki_endpoint(req: WikiSaveRequest):
    from src.ontology.wiki_manager import save_wiki
    result = save_wiki(
        product_line=req.product_line,
        from_class=req.source,
        rel_name=req.rel,
        to_class=req.target,
        content=req.content,
        editor=req.editor,
    )
    return result


@router.post("/api/wiki/generate-one")
async def generate_one_wiki(req: WikiGenerateOneRequest):
    from src.ontology.wiki_manager import generate_wiki_for_relationship_stream
    
    async def generate():
        full_content = ""
        try:
            async for chunk in generate_wiki_for_relationship_stream(
                product_line=req.product_line,
                from_class=req.source,
                rel_name=req.rel,
                to_class=req.target,
                cardinality=req.cardinality,
                description=req.description,
            ):
                full_content += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
            
            # Clean matching the logic inside wiki_manager
            cleaned = full_content.strip()
            if cleaned.startswith("```markdown"):
                cleaned = cleaned[len("```markdown"):].strip()
            elif cleaned.startswith("```md"):
                cleaned = cleaned[len("```md"):].strip()
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:].strip()
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()

            yield f"data: {json.dumps({'type': 'done', 'content': cleaned}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/api/wiki/generate-batch")
async def generate_batch_wiki(req: WikiGenerateBatchRequest):
    from src.ontology.wiki_manager import collect_all_relationships, generate_wiki_for_relationship
    import time as _time

    relationships = collect_all_relationships()
    total = len(relationships)

    def progress_stream():
        generated = 0
        skipped = 0
        failed = 0

        for i, rel in enumerate(relationships):
            result = generate_wiki_for_relationship(
                product_line=req.product_line,
                from_class=rel["fromClass"],
                rel_name=rel["relationName"],
                to_class=rel["toClass"],
                cardinality=rel.get("cardinality", ""),
                description=rel.get("description", ""),
                overwrite=req.overwrite,
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

            progress = {
                "type": "progress",
                "index": i + 1,
                "total": total,
                "relationship": f"{rel['fromClass']}_{rel['relationName']}_{rel['toClass']}",
                "status": status,
                "generated": generated,
                "skipped": skipped,
                "failed": failed,
            }
            yield f"data: {json.dumps(progress, ensure_ascii=False)}\n\n"

            if result.get("generated"):
                _time.sleep(0.3)

        summary = {
            "type": "done",
            "total": total,
            "generated": generated,
            "skipped": skipped,
            "failed": failed,
        }
        yield f"data: {json.dumps(summary, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        progress_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/api/wiki/stats")
def wiki_stats(product_line: str = None):
    from src.ontology.wiki_manager import get_wiki_stats
    return get_wiki_stats(product_line)


@router.get("/api/wiki/relationships")
def list_all_relationships():
    from src.ontology.wiki_manager import collect_all_relationships
    return {"relationships": collect_all_relationships()}
