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

def verify_scheduling_route_connection():
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
            "name": "SchedulingRoute -> Product (BELONGS_TO_PRODUCT)",
            "cypher": """
            MATCH (r:OntologyClass {name: "SchedulingRoute"})-[rel:ONTOLOGY_RELATION {name: "BELONGS_TO_PRODUCT"}]->(t:OntologyClass {name: "Product"})
            RETURN r.name AS source, type(rel) AS rel_type, rel.name AS relation_name, t.name AS target, rel.description AS desc
            """
        },
        {
            "name": "Workflow -> SchedulingRoute (HAS_SCHEDULING_ROUTE)",
            "cypher": """
            MATCH (r:OntologyClass {name: "Workflow"})-[rel:ONTOLOGY_RELATION {name: "HAS_SCHEDULING_ROUTE"}]->(t:OntologyClass {name: "SchedulingRoute"})
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
    verify_scheduling_route_connection()
