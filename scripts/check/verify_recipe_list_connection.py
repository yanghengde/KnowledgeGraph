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

def verify_recipe_list_connection():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")

    if not all([uri, user, password]):
        print("Neo4j 环境变量未在 .env 中完整配置")
        return

    print("Connecting to Neo4j database...")
    driver = GraphDatabase.driver(uri, auth=(user, password))

    # 修正属性名为 name，而非 relationName
    query = """
    MATCH (rl:OntologyClass {name: "RecipeList"})-[r:ONTOLOGY_RELATION {name: "ASSOCIATED_RECIPE"}]->(recipe:OntologyClass {name: "Recipe"})
    RETURN rl.name AS source, type(r) AS rel_type, r.name AS relation_name, recipe.name AS target, r.description AS desc
    """

    try:
        with driver.session() as session:
            result = session.run(query)
            records = list(result)
            
            print(f"\n验证结果: 共找到 {len(records)} 个从 RecipeList 到 Recipe 的直接关联关系\n")
            if len(records) == 0:
                print("[WARNING] 没有找到 RecipeList -> Recipe 的直接关联关系，请检查本体加载状态！")
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
    verify_recipe_list_connection()
