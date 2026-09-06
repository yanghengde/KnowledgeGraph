import os
import sys
import glob
import json
from dotenv import load_dotenv

# Ensure project root is in path for 'src' imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

# Explicit container/process environment must win over a developer's local file.
load_dotenv(os.path.join(PROJECT_ROOT, ".env"), override=False)

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
