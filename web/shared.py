import os
import sys
import glob
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Ensure project root is in path for 'src' imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

# Explicit container/process environment must win over a developer's local file.
load_dotenv(os.path.join(PROJECT_ROOT, ".env"), override=False)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# ── Chat session memory ──
_chat_sessions = {}

# ── Lazy-loaded vector collection ──
import threading
_vector_collection = None
_vector_lock = threading.Lock()

def _get_vector_collection():
    global _vector_collection
    if _vector_collection is None:
        with _vector_lock:
            if _vector_collection is None:
                try:
                    from src.qa.vectorizer import get_vector_collection
                    _vector_collection = get_vector_collection()
                    print(f"[Chat] Vector store loaded: {_vector_collection.count()} chunks")
                except Exception as e:
                    print(f"[Chat] Vector store not available: {e}")
    return _vector_collection

# SQL mode does not use ChromaDB. Keep the collection lazy so starting the
# graph viewer neither writes to the tracked vector database nor consumes
# memory before a non-SQL assistant explicitly requests vector retrieval.

# ── Module combos classification ──
MODULE_MAP = {}

def _load_module_map(force_reload: bool = False):
    global MODULE_MAP
    if MODULE_MAP and not force_reload:
        return
        
    MODULE_MAP.clear()
    kb_path = os.path.join(PROJECT_ROOT, "src", "ontology", "wiki_kb")
    json_files = glob.glob(os.path.join(kb_path, "*_ontology.json"))
    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                filename = os.path.basename(file_path)
                module_id = filename.replace("_ontology.json", "")
                
                for cls in data.get("classes", []):
                    if module_id != "cross_module":
                        MODULE_MAP[cls["className"]] = module_id
        except Exception as e:
            print(f"Error loading {file_path} for MODULE_MAP: {e}")

_load_module_map()

def _classify_module(class_name: str) -> str:
    if class_name.startswith("BusinessProcess") or class_name == "BPSpecBizRuleTxnMap":
        return "change_management"

    lower = class_name.lower()
    if "workflow" in lower or "path" in lower or "selector" in lower:
        return "workflow"
    
    val = MODULE_MAP.get(class_name, "other")
    if val == "uoms":
        return "other"
    if val == "training_plan":
        return "employee"
    if val == "switching_rules":
        return "sampling"
    if val == "aql_levels":
        return "sampling"
    if val == "start_reasons":
        return "container"
    if val == "bonus_reasons":
        return "operation"
    if val == "buy_reasons":
        return "operation"
    if val == "business_process":
        return "change_management"
    return val
