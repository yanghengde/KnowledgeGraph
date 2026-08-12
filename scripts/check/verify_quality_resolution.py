import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

# 加载 .env
load_dotenv()

def verify_quality_resolution():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")

    if not all([uri, user, password]):
        print("Neo4j 环境变量未在 .env 中完整配置")
        return

    print("Connecting to Neo4j database...")
    driver = GraphDatabase.driver(uri, auth=(user, password))

    query = """
    MATCH (q:OntologyClass {name: "QualityResolutionCode"})-[r]-(target)
    RETURN q.name AS source, type(r) AS rel_type, target.name AS target_name, r.description AS desc
    """

    try:
        with driver.session() as session:
            result = session.run(query)
            records = list(result)
            
            print(f"\n验证结果: 共找到 {len(records)} 个与 QualityResolutionCode 关联的本体连接\n")
            if len(records) == 0:
                print("⚠️ 警告: QualityResolutionCode 节点仍然是孤立状态，没有找到关联！")
            else:
                print(f"{'Source Class':<25} | {'Relationship':<25} | {'Target Class':<25}")
                print("-" * 85)
                for r in records:
                    print(f"{r['source']:<25} | {r['rel_type']:<25} | {r['target_name']:<25}")
                    print(f"  └─ 描述: {r['desc']}\n")
    except Exception as e:
        print(f"执行 Cypher 查询失败: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    verify_quality_resolution()
