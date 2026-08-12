// ── 创建约束 ──
CREATE CONSTRAINT FOR (n:WorkflowDef)        REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT FOR (n:StepDef)            REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT FOR (n:OperationDef)       REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT FOR (n:ProductDef)         REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT FOR (n:ResourceDef)        REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT FOR (n:ESpecDef)           REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT FOR (n:DataCollectionDef)  REQUIRE n.name IS UNIQUE;

// ── 创建本体元数据节点（描述类本身） ──
CREATE (:OntologyClass {
    name: 'WorkflowDef',
    layer: 'Config',
    chineseName: '工艺路线',
    sourceTable: 'Workflows',
    description: 'Camstar工艺路线定义，包含一组有序的工步'
});

CREATE (:OntologyClass {
    name: 'ESpecDef',
    layer: 'Config',
    chineseName: '参数规格',
    sourceTable: 'ESpecs',
    description: '定义工步数据采集的参数规格，含上下限'
});

// ── 示例：建立本体类层级关系 ──
MATCH (wf:OntologyClass {name:'WorkflowDef'})
MATCH (st:OntologyClass {name:'StepDef'})
CREATE (wf)-[:ONTOLOGY_RELATION {
    name: 'HAS_STEP',
    cardinality: 'ONE_TO_MANY',
    ordered: true,
    orderField: 'sequence'
}]->(st);
