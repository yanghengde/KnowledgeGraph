import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# DeepSeek API config
API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

def read_wiki_document(filepath: str) -> str:
    """Read a document from the wiki knowledge base."""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def generate_ontology_from_wiki(wiki_content: str, module_name: str) -> dict:
    """Use DeepSeek LLM to generate an ontology draft from WIKI content."""
    prompt = f"""
    你是一个经验丰富的 Camstar MES 领域专家和本体工程师。
    下面是 Camstar {module_name} 模块的官方文档或知识内容：
    
    ======================================
    {wiki_content}
    ======================================
    
    请根据这些文档内容，提取该模块的本体类定义（Ontology Class）、属性（Property）和关系（Relationship）。
    请以 JSON 格式输出，JSON 应包含以下结构：
    {{
        "module": "{module_name}",
        "classes": [
            {{
                "className": "英文类名（如 WorkflowDef）",
                "chineseName": "中文描述",
                "description": "类的业务含义",
                "properties": [
                    {{"name": "属性名", "type": "String/Integer/Float/Date/Boolean", "description": "描述"}}
                ]
            }}
        ],
        "relationships": [
            {{
                "fromClass": "源类",
                "toClass": "目标类",
                "relationName": "关系名称（全大写如 HAS_STEP）",
                "cardinality": "ONE_TO_MANY/ONE_TO_ONE",
                "description": "业务含义"
            }}
        ]
    }}
    请直接返回 JSON 数据，不要包含其他解释信息。
    """
    
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "You are a professional Camstar ontology extraction tool. Output strictly valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )
    
    content = response.choices[0].message.content.strip()
    
    # Strip markdown block quotes if present
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
        
    if content.endswith("```"):
        content = content[:-3]
        
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON from LLM: {e}")
        print("Raw output:")
        print(content)
        return {}

def map_ontology_to_db_schema(ontology_json: dict, db_schema_info: str) -> dict:
    """Use LLM to map the generated ontology to actual Database Tables/Columns."""
    prompt = f"""
    你现在需要将本体定义与数据库表结构进行映射。
    
    已生成的本体：
    {json.dumps(ontology_json, ensure_ascii=False)}
    
    对应的 Camstar 数据库结构信息（INFORMATION_SCHEMA 扫描结果）：
    {db_schema_info}
    
    请输出映射结果（JSON格式），将 ontology 的类映射到表，属性映射到字段：
    [
        {{
            "ontologyClass": "类名",
            "sourceTable": "对应的表名",
            "properties": [
                {{"ontologyProperty": "本体属性", "sourceColumn": "对应的数据库字段"}}
            ]
        }}
    ]
    直接返回 JSON 格式结果。
    """
    
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "You are a professional DB mapper. Output strictly valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )
    
    content = response.choices[0].message.content.strip()
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
        
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {}

if __name__ == "__main__":
    wiki_path = os.path.join(os.path.dirname(__file__), "wiki_kb", "workflow_modeling.md")
    output_path = os.path.join(os.path.dirname(__file__), "wiki_kb", "workflow_ontology.json")
    
    if os.path.exists(wiki_path):
        print(f"Reading {wiki_path}...")
        content = read_wiki_document(wiki_path)
        print("Sending to DeepSeek LLM for ontology extraction (this may take a minute)...")
        ontology = generate_ontology_from_wiki(content, "Workflow Modeling")
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(ontology, f, indent=4, ensure_ascii=False)
            
        print(f"Ontology extracted and saved to {output_path}")
    else:
        print(f"Wiki document not found at {wiki_path}")
