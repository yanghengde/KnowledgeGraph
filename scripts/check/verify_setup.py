import os
import sys
from dotenv import load_dotenv
from neo4j import GraphDatabase

# 强制将标准输出设置为 utf-8，解决 Windows 下 GBK 编码报错问题
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        # 兼容旧版本 python
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 加载 .env
load_dotenv()

def verify_setup_connection():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")

    if not all([uri, user, password]):
        print("Neo4j 环境变量未在 .env 中完整配置")
        return

    print("Connecting to Neo4j database...")
    driver = GraphDatabase.driver(uri, auth=(user, password))

    # 验证关系列表
    queries = [
        {
            "name": "Setup -> ResourceGroup (BELONGS_TO_GROUP)",
            "cypher": """
            MATCH (r:OntologyClass {name: "Setup"})-[rel:ONTOLOGY_RELATION {name: "BELONGS_TO_GROUP"}]->(t:OntologyClass {name: "ResourceGroup"})
            RETURN r.name AS source, type(rel) AS rel_type, rel.name AS relation_name, t.name AS target, rel.description AS desc
            """
        },
        {
            "name": "Setup -> DocumentSet (HAS_DOCUMENT_SET)",
            "cypher": """
            MATCH (r:OntologyClass {name: "Setup"})-[rel:ONTOLOGY_RELATION {name: "HAS_DOCUMENT_SET"}]->(t:OntologyClass {name: "DocumentSet"})
            RETURN r.name AS source, type(rel) AS rel_type, rel.name AS relation_name, t.name AS target, rel.description AS desc
            """
        },
        {
            "name": "Spec -> Setup (REQUIRES_SETUP)",
            "cypher": """
            MATCH (r:OntologyClass {name: "Spec"})-[rel:ONTOLOGY_RELATION {name: "REQUIRES_SETUP"}]->(t:OntologyClass {name: "Setup"})
            RETURN r.name AS source, type(rel) AS rel_type, rel.name AS relation_name, t.name AS target, rel.description AS desc
            """
        },
        {
            "name": "Product -> Setup (REQUIRES_SETUP)",
            "cypher": """
            MATCH (r:OntologyClass {name: "Product"})-[rel:ONTOLOGY_RELATION {name: "REQUIRES_SETUP"}]->(t:OntologyClass {name: "Setup"})
            RETURN r.name AS source, type(rel) AS rel_type, rel.name AS relation_name, t.name AS target, rel.description AS desc
            """
        },
        {
            "name": "Resource -> Setup (CURRENT_SETUP)",
            "cypher": """
            MATCH (r:OntologyClass {name: "Resource"})-[rel:ONTOLOGY_RELATION {name: "CURRENT_SETUP"}]->(t:OntologyClass {name: "Setup"})
            RETURN r.name AS source, type(rel) AS rel_type, rel.name AS relation_name, t.name AS target, rel.description AS desc
            """
        }
    ]

    try:
        with driver.session() as session:
            for q in queries:
                print(f"\n正在验证: {q['name']} ...")
                result = session.run(q["cypher"])
                records = list(result)
                
                print(f"验证结果: 共找到 {len(records)} 个本体关联")
                if len(records) == 0:
                    print(f"[WARNING] 没有找到 {q['name']} 的直接本体关联关系，请检查本体加载状态！")
                else:
                    print(f"{'Source Class':<20} | {'Relation Name':<20} | {'Target Class':<20}")
                    print("-" * 70)
                    for r in records:
                        print(f"{r['source']:<20} | {r['relation_name']:<20} | {r['target']:<20}")
                        print(f"  └─ 描述: {r['desc']}")
    except Exception as e:
        print(f"执行 Cypher 查询失败: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    verify_setup_connection()
