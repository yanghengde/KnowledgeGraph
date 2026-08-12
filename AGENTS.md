# CamstarOntology — 开发指南

## 项目简介

CamstarOntology 是 Siemens Opcenter Execution (Camstar) MES 系统的知识图谱项目。将 Camstar 建模对象（API 实体）映射为本体图谱（Ontology Graph），存储于 Neo4j 图数据库，并通过 G6 v5 前端可视化展示。

## 目录结构

```
CamstarOntology/
├── docs/                         # 物理数据库架构定义及参考文档
│   ├── Database_Tables.csv       # 物理数据库表定义（CDO列表，只读事实来源）
│   ├── Database_Fields.csv       # 物理数据库字段与外键关联（只读事实来源）
│   └── ...
├── src/
│   ├── ontology/
│   │   ├── wiki_kb/              # 本体图谱核心目录
│   │   │   ├── *_ontology.json   # 实体定义：类、属性、关系
│   │   │   ├── *_modeling.md     # 实体文档（中文 + 英文）
│   │   │   └── cross_module_ontology.json  # 跨模块关系汇总
│   │   ├── loader/
│   │   │   └── neo4j_loader.py   # Neo4j 批量导入脚本
│   │   └── wiki_manager.py       # Wiki 管理工具
│   └── Swagger/                  # Camstar API Swagger 定义（系统生成，只读参考，非核心）
├── web/                          # G6 v5 前端可视化
│   ├── static/app.js             # 图谱渲染 + 模块颜色配置
│   └── server.py                 # Flask API 服务器
├── scripts/etl/                  # ETL 数据管道脚本
├── .env                          # Neo4j 连接配置（不入库）
└── AGENTS.md                     # 本文件
```

## 核心工作流

### 1. 新增本体实体

**步骤：**

1. **定位物理表与字段**：在 `docs/Database_Tables.csv` 中查找实体对应的 `CDOName`（即物理表名，对应本体的 className）。随后在 `docs/Database_Fields.csv` 中过滤出该 `CDOName` 对应的所有物理字段。
2. **提取字段 Schema 与关系**：从 `Database_Fields.csv` 中提取字段属性，区分以下类型：
   - **普通数据属性**：根据 `DataType` 映射（如 `IsFrozen` -> Boolean, `Notes` -> String, `IconId` -> Integer），字段名称转换为 camelCase 格式。
   - **外键与导航属性**：若 `IsForeignKey` 为 `True` 且有 `FKTableName`，则该字段为物理外键（如 `SetupAccessId` 指向 `A_SetupAccess`）。在本体中，应剥离其后缀（如剥离 `Id`, `DefId`, `RefId` 后缀），转换为 camelCase，且类型必须标注为 `"type": "Navigation"`。
   - **过滤系统字段**：跳过 `CDOTypeId`、`ChangeCount`、`ExportImportKey` 等内置基础设施字段。
3. **创建 `*_ontology.json`**：按标准格式编写类定义，正确声明普通字段和 Navigation 类型的关联。
4. **创建 `*_modeling.md`**：编写对应的中英文建模说明文档。
5. **注册到加载器**：在 `src/ontology/loader/neo4j_loader.py` 的 `files_to_load` 列表中按字母顺序加入新文件。
6. **添加关系定义**：如果该实体包含外键（Navigation）或与其他实体存在关联，在 `cross_module_ontology.json` 或本模块的 `relationships` 数组中添加对应的本体关系定义。
7. **运行物理一致性校验**：执行 `validate_ontology_vs_csv.py` 校验脚本，验证新建的本体与物理 CSV 的对齐程度，确保无缺失字段、类型错误或关系遗漏。
8. **加载到 Neo4j**：运行 `python src/ontology/loader/neo4j_loader.py` 加载并同步到图数据库。

**重要规则：**
- **绝不修改 `docs/Database_Tables.csv` 和 `docs/Database_Fields.csv`**，它们是物理数据库 Schema 的唯一事实来源。
- 本体字段名转换为 camelCase 时，必须与校验器中的后缀剥离规范化规则（去除 `Id`/`DefId`/`RefId` 后缀后转全小写）保持一致，以确保物理对齐校验成功。
- 所有外键字段均采用 `"type": "Navigation"` 映射。

### 2. 检查/修复已有本体

1. 运行 `validate_ontology_vs_csv.py` 校验脚本，生成模块级物理一致性校验报告（通常输出到 `docs/ontology_csv_validation_report.md`）。
2. 根据报告中提示的 `Missing Navigation Properties`（缺失物理外键）、`Property Type Mismatches`（类型不匹配）或 `Missing Relationships`（缺失关系），对比 `docs/Database_Fields.csv`。
3. 修正 `*_ontology.json` 和 `cross_module_ontology.json` 中的字段定义或关系，使其与物理数据库对齐。
4. 重新运行校验脚本，直至该模块的物理对齐警告降为 **0**。
5. 运行 `python src/ontology/loader/neo4j_loader.py` 重新加载。

### 3. 实体分类与字段模式

**简单目录实体** — 只有基础字段：
```json
{"name": "name", "type": "String", "required": true},
{"name": "description", "type": "String"},
{"name": "notes", "type": "String"},
{"name": "filterTags", "type": "String"},
{"name": "isFrozen", "type": "Boolean"},
{"name": "instanceLocked", "type": "Boolean"},
{"name": "changeHistory", "type": "Navigation"},
{"name": "iconId", "type": "Integer"}
```

**分组容器实体** — 额外的 entries/groups 字段：
```json
{"name": "entryType", "type": "String"},
{"name": "entries", "type": "SubentityList", "description": "... → SomeEntity"},
{"name": "groups", "type": "SubentityList", "description": "... → SelfRefGroup"},
{"name": "defaultForObjectTypes", "type": "Array"}
```
关系：`Group -[HAS_ENTRY]-> Entry`、`Group -[HAS_SUBGROUP]-> Group`

**版本控制实体**（base CDOName 对应 revisioned 实体，如 base CdoId: 3620）— 额外的 revision 字段：
```json
{"name": "revision", "type": "String", "required": true},
{"name": "isRevOfRcd", "type": "Boolean"},
{"name": "canChangeRevOfRcd", "type": "Boolean"},
{"name": "eco", "type": "String"},
{"name": "status", "type": "Integer", "description": "1=Active, 2=Inactive"},
{"name": "setupAccess", "type": "Navigation"},
{"name": "wipMsgDefMgr", "type": "Navigation"},
{"name": "base", "type": "Navigation"},
{"name": "associatedPackages", "type": "Integer"}
```

### 4. Neo4j 连接

配置在 `.env` 文件中：
```
NEO4J_URI=bolt://...
NEO4J_USER=...
NEO4J_PASSWORD=...
```

加载命令：`python src/ontology/loader/neo4j_loader.py`

## 已完成的本体模块

当前已加载约 100+ 个模块，涵盖：
- **工作流**: Workflow, WorkflowStep, PhaseTemplate, PlanTemplate, ProcessModelTemplate
- **工序**: Operation, Spec, WorkCenter, BillOfProcess
- **工厂**: Factory, MfgLine, MfgCalendar, Enterprise
- **设备**: Part, PartFamily, Resource, ResourceGroup, ResourceType, ResourceStatusModel
- **人员**: Employee, Role, Owner, Team, Shift
- **质量**: Event, CAPA, Classification, Subclassification, QualityResolutionCode
- **物料**: Product, ProductFamily, BOM, ERPBOM, Material
- **工装**: Tool, ToolFamily, ToolGroup, ToolPlan
- **组织**: Organization, CategoryMap, OrgNotification, EventClassificationSpecMap
- **变更管理**: ChangeManagement, PackageCreationTemplate, PackageType, CollaboratorTemplate
- **培训**: TrainingPlan, TrainingRequirement, TrainingReqGroup
- **原因代码**: PauseReason, ReworkReason, ScrapReason, ShippingReason 等 + 对应 Group
- **其他**: Checklist, Document, Label, PrintQueue, Sampling, Supplier, Vendor...
