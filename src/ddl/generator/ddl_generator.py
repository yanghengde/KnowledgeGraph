from neo4j import GraphDatabase

TYPE_MAP = {
    'String':   'NVARCHAR(200)',
    'Text':     'NVARCHAR(MAX)',
    'Integer':  'INT',
    'Float':    'DECIMAL(18,6)',
    'Boolean':  'BIT',
    'DateTime': 'DATETIME',
    'Date':     'DATE'
}

def generate_ddl_from_ontology(driver) -> str:
    """读取 Neo4j 本体，生成 SQL Server DDL"""
    ddl_statements = []

    with driver.session() as session:
        # 查询所有本体类及其属性
        classes = session.run("""
            MATCH (c:OntologyClass)
            OPTIONAL MATCH (c)-[:HAS_PROPERTY]->(p:OntologyProperty)
            RETURN c.name AS class_name,
                   c.layer AS layer,
                   collect({
                       name: p.name,
                       dataType: p.dataType,
                       required: p.required
                   }) AS properties
            ORDER BY c.layer, c.name
        """)

        for record in classes:
            class_name = record['class_name']
            properties = record['properties']

            cols = [f"    {class_name.lower()}_id  NVARCHAR(200) PRIMARY KEY"]
            for prop in properties:
                if not prop['name']:
                    continue
                sql_type = TYPE_MAP.get(prop['dataType'], 'NVARCHAR(200)')
                nullable = '' if prop.get('required') else ' NULL'
                cols.append(f"    {prop['name'].lower():<30} {sql_type}{nullable}")

            # 标准审计列
            cols.append("    _source_id    NVARCHAR(200) NULL")
            cols.append("    _loaded_at    DATETIME      NOT NULL DEFAULT GETDATE()")

            ddl = (
                f"-- {class_name} ({record['layer']} Layer)\n"
                f"CREATE TABLE ont_{class_name} (\n"
                + ',\n'.join(cols)
                + "\n);\n"
            )
            ddl_statements.append(ddl)

        # 查询外键关系
        relations = session.run("""
            MATCH (from:OntologyClass)-[r:ONTOLOGY_RELATION]->(to:OntologyClass)
            WHERE r.cardinality IN ['MANY_TO_ONE', 'ONE_TO_ONE']
            RETURN from.name AS from_class,
                   to.name   AS to_class,
                   r.name    AS rel_name
        """)

        fk_statements = []
        for rel in relations:
            fk = (
                f"ALTER TABLE ont_{rel['from_class']} "
                f"ADD CONSTRAINT fk_{rel['from_class']}_{rel['to_class']} "
                f"FOREIGN KEY ({rel['to_class'].lower()}_id) "
                f"REFERENCES ont_{rel['to_class']} ({rel['to_class'].lower()}_id);"
            )
            fk_statements.append(fk)

    return '\n\n'.join(ddl_statements) + '\n\n-- Foreign Keys\n' + '\n'.join(fk_statements)
