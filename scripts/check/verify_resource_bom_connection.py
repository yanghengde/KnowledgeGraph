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

def verify_resource_bom_connection():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")

    if not all([uri, user, password]):
        print("Neo4j 环境变量未在 .env 中完整配置")
        return

    print("Connecting to Neo4j database...")
    driver = GraphDatabase.driver(uri, auth=(user, password))

    # 验证 Resource -[HAS_BOM]-> ResourceBOM 本体关系
    query = """
    MATCH (r:OntologyClass {name: "Resource"})-[rel:ONTOLOGY_RELATION {name: "HAS_BOM"}]->(b:OntologyClass {name: "ResourceBOM"})
    RETURN r.name AS source, type(rel) AS rel_type, rel.name AS relation_name, b.name AS target, rel.description AS desc
    """

    try:
        with driver.session() as session:
            result = session.run(query)
            records = list(result)
            
            print(f"\n验证结果: 共找到 {len(records)} 个从 Resource 到 ResourceBOM 的直接本体关联关系\n")
            if len(records) == 0:
                print("[WARNING] 没有找到 Resource -> ResourceBOM 的直接本体关联关系，请检查本体加载状态！")
            else:
                print(f"{'Source Class':<20} | {'Relation Name':<20} | {'Target Class':<20}")
                print("-" * 70)
                for r in records:
                    print(f"{r['source']:<20} | {r['relation_name']:<20} | {r['target']:<20}")
                    print(f"  └─ 描述: {r['desc']}\n")
    except Exception as e:
        print(f"执行 Cypher 查询失败: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    verify_resource_bom_connection()
