import os
import sys

# Ensure project root is in sys.path so 'web' package can be imported
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from web.shared import PROJECT_ROOT


app = FastAPI(title="Opcenter Manufacturing Graph Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=5)

# Mount static files directory
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

# Import and mount decoupled API routers
from web.routers.graph import router as graph_router
from web.routers.sql_builder import router as sql_builder_router
from web.routers.ontology_import import router as ontology_import_router
from web.routers.semantic_mapping import router as semantic_mapping_router
from web.routers.ontology_authority import router as ontology_authority_router
from web.routers.sync_center import router as sync_center_router
from web.routers.manufacturing_chat import router as manufacturing_chat_router

app.include_router(graph_router)
app.include_router(sql_builder_router)
app.include_router(ontology_import_router)
app.include_router(semantic_mapping_router)
app.include_router(ontology_authority_router)
app.include_router(sync_center_router)
app.include_router(manufacturing_chat_router)


@app.get("/")
def index():
    return RedirectResponse("/app/overview")


@app.get("/sync")
def sync_center():
    return RedirectResponse("/app/overview")


@app.get("/ontology")
def ontology_explorer():
    return RedirectResponse("/app/ontology-model")


@app.get("/chat")
@app.get("/knowledge-chat")
def manufacturing_knowledge_chat():
    return RedirectResponse("/app/assistant")


@app.get("/app")
@app.get("/app/{frontend_path:path}")
def manufacturing_console(frontend_path: str = ""):
    """Serve the manufacturing console."""
    index_path = os.path.join(os.path.dirname(__file__), "static", "react", "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(
            status_code=503,
            detail="React console is not built. Run npm install and npm run build in frontend/.",
        )
    return FileResponse(index_path)


@app.get("/healthz", include_in_schema=False)
def healthz():
    from sqlalchemy import text
    from src.graphstudio_sync.config import SyncSettings
    from src.graphstudio_sync.storage.database import control_engine

    try:
        engine = control_engine(SyncSettings.from_env())
        with engine.connect() as connection:
            connection.execute(text("SELECT 1 FROM graphsync.schema_version LIMIT 1"))
        engine.dispose()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="PostgreSQL control plane is unavailable") from exc
    return {"status": "ok", "service": "opcenter-graph-sync", "dependencies": {"postgresql": "online"}}


if __name__ == "__main__":
    import uvicorn

    # Reloading the whole repository is unsafe for this service: a Graph Studio
    # deployment writes TTL/ZIP artifacts below outputs/, which used to make the
    # development reloader restart the API in the middle of a publish.  Keep
    # reload opt-in and, when requested, watch source directories only.
    reload_enabled = os.getenv("WEB_RELOAD", "false").strip().casefold() in {
        "1", "true", "yes", "on",
    }
    host = os.getenv("WEB_HOST", "0.0.0.0").strip() or "0.0.0.0"
    port = int(os.getenv("WEB_PORT", "5050"))
    print(
        f"Starting Camstar Ontology Graph Viewer (FastAPI) on http://{host}:{port} "
        f"(reload={'enabled' if reload_enabled else 'disabled'})"
    )
    uvicorn.run(
        "web.server:app",
        host=host,
        port=port,
        reload=reload_enabled,
        reload_dirs=(
            [str(os.path.join(PROJECT_ROOT, "web")), str(os.path.join(PROJECT_ROOT, "src"))]
            if reload_enabled
            else None
        ),
    )
