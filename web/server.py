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
from fastapi.responses import FileResponse
from web.shared import PROJECT_ROOT


app = FastAPI(title="Camstar Ontology API")

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
from web.routers.wiki import router as wiki_router
from web.routers.chat import router as chat_router
from web.routers.sql_builder import router as sql_builder_router
from web.routers.i18n import router as i18n_router
from web.routers.ontology_import import router as ontology_import_router

app.include_router(graph_router)
app.include_router(wiki_router)
app.include_router(chat_router)
app.include_router(sql_builder_router)
app.include_router(i18n_router)
app.include_router(ontology_import_router)


@app.get("/")
def index():
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))


@app.get("/healthz", include_in_schema=False)
def healthz():
    from web.shared import driver

    try:
        driver.verify_connectivity()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Neo4j is unavailable") from exc
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    print("Starting Camstar Ontology Graph Viewer (FastAPI) on http://0.0.0.0:5050")
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=5050,
        reload=True,
        reload_dirs=[PROJECT_ROOT],
        reload_excludes=["*.md", "*.json", "*.jsonl", "*.csv", "*.log", "*.sqlite3", "*relationships*", "*wiki_kb*", "*logs*", "*scratch*"]
    )
