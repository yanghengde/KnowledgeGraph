# Siemens Opcenter MES (Camstar) 本体知识图谱 & Graph-RAG 智能协作平台

> **基于 Siemens Opcenter Execution (Camstar) 建模逻辑的全栈知识图谱及 Graph-RAG 智能协作问答系统。**

本平台是一个专为制造执行系统 (MES) 领域设计的全栈知识图谱与智能问答应用。系统将 Camstar 的建模对象（如在制品 Container、工序 Spec、工作中心 WorkCenter、工艺路线 Workflow 等）映射为本体图谱（Ontology Graph），并利用 **Neo4j 图数据库**进行存储。前端采用最新的 **AntV G6 v5** 提供高性能的可视化拓扑呈现，并整合 **DeepSeek LLM** 与 **ChromaDB 本地向量库**，构建支持行业/产品线隔离的 **Graph-RAG 智能问答**。

---

## 🌟 核心特性与业务价值

### 1. 全面的 MES 核心本体建模（100+ 模块）

* **业务域覆盖**：当前图谱包含 **593 个业务类、8337 个属性和 1590 条关系**，覆盖 Workflow (工艺路线)、Operation (工序交易)、Spec (规范)、WorkCenter (工作中心)、Product (产品及家族)、Quality (品质事件/CAPA)、BOM/ERPBOM、Resource (资源/机台)、Employee/Role (人员与角色) 以及 **SPC (统计过程控制)** 等核心物理与逻辑建模对象。
* **物理一致性对齐**：本体严格遵循物理数据库定义。通过 `docs/Database_Tables.csv` (CDO列表) 与 `docs/Database_Fields.csv` (字段定义) 作为唯一事实来源开展映射。字段自动转为 camelCase 驼峰命名，外键字段规范化映射为 `Navigation` 类型。

### 2. 行业/产品线隔离与参数化支持

* **多行业隔离**：支持新能源电池 (Battery)、汽车装配 (Automotive)、通用制造 (General) 等多条典型产品线/行业的配置，系统默认以 `general` (通用/基准) 行业作为缺省配置。
* **行业参数对齐**：关系 Wiki 与 RAG 问答背景均与当前选定的行业强关联，实现参数化与定制化。

### 3. Graph-RAG 流式智能问答 (RAG Co-Pilot)

* **流式 SSE 交互**：问答助手采用 Server-Sent Events (SSE) 协议，实现 DeepSeek 模型超低延迟的流式文字打字机输出。
* **智能图谱检索**：深度集成 Neo4j Cypher 拓扑关系检索与 ChromaDB 向量语义匹配。问答引擎自动解析用户提问，提取本体节点关键字，从 Neo4j 中拉取局部子图定义注入 Prompt，大幅降低大模型的幻觉率。
* **原生节点提及 (@Mention)**：聊天输入框支持键入 `@` 字符触发实时联想下拉，允许模糊搜索当前图谱中的 500+ 个类节点。选中后插入 `[[ClassName]]` 特征标记，指引问答引擎优先提取该类在图谱中的邻居子图及字段语义。

### 4. 极致渲染与性能优化

* **前端差量渲染更新 (`_applyStates`)**：摒弃传统的全量重绘机制。引入状态对比缓存，每次点击仅对发生改变的节点及连线应用高亮/置灰等样式变化，点击响应时间从 300ms 骤降至 **< 30ms**。
* **大规模视口裁剪 (Viewport Culling)**：在 G6 图谱渲染中，视口之外的文字标签和阴影效果会自动裁剪并隐藏，只在 Hover 时动态加载，支持 500+ 节点、1500+ 边的流畅渲染。
* **UNWIND 批量数据装载**：Neo4j 数据导入完全重构为 Cypher `UNWIND` 批量装载机制。装载网络往返开销降低 99.9%，支持全部本体快速部署入库。

### 5. 平台设置、物理结构导入与在线维护

* **中英文热切换**：平台界面支持简体中文与英文即时切换，无需重启服务；节点名、关系名和属性技术字段名始终保持原名，避免翻译破坏物理 Schema 语义。
* **描述独立翻译**：以节点为入口维护节点描述和所属属性描述。可从 Camstar Designer CDO 元数据同步英文描述，并按当前界面语言显示中文翻译或英文原文。
* **受审核 CSV 导入**：在“平台设置 → 图谱导入”中分别上传表定义 CSV 和字段定义 CSV。现有图谱节点视为已审核对象，新发现 CDO 默认不导入，必须人工判断其是否具有独立业务意义后才能写入。
* **独立图谱维护**：在“平台设置 → 图谱维护”中提供一键清空。操作前会展示影响规模，并要求勾选不可撤销声明及输入完整确认词；清空后进入持久化空图谱模式，适合从零重新审核和导入。
* **行业设置内嵌**：行业/产品线配置已经整合进平台设置，不再跳转到独立页面，保存后即时影响产品线选择与关系 Wiki 上下文。

---

## 🏗️ 系统架构

系统由前端展示层、FastAPI 路由网关、本体定义层、双数据库（Neo4j 图数据库 + ChromaDB 向量数据库）及 LLM 推理引擎共同构成：

```
                              ┌─────────────────────────────────────────────────────────────┐
                              │                       前端浏览器 (Browser)                   │
                              │      ┌─────────────────┐       ┌────────────────┐            │
                              │      │  G6 拓扑图谱     │       │ 问答助手       │            │
                              │      │  (app.js WebGL) │       │ (流式 @Mention)│            │
                              │      └─────────────────┘       └────────────────┘            │
                              └──────────────────────────────┬──────────────────────────────┘
                                                             │ HTTP / SSE (FastAPI Port: 5050)
                              ┌──────────────────────────────┴──────────────────────────────┐
                              │                    FastAPI Web Server (server.py)           │
                              │ /api/graph/*  /api/wiki/*  /api/chat/*  /api/i18n/*         │
                              │                /api/ontology-import/*                         │
                              └───────────┬───────────────────┬───────────────────┬─────────┘
                                          │                   │                   │
                     ┌────────────────────┴───┐    ┌──────────┴──────────┐   ┌────┴───────────────┐
                     │   Neo4j 图数据库        │    │ ChromaDB 本地向量库  │   │  DeepSeek LLM API  │
                     │ (593 类, 1590 条关系)   │    │    (文档章节)       │   │  (流式多轮对话生成)  │
                     │  规范索引: 10 大约束   │    │ 路径: data/vector_  │   │                    │
                     │                        │    │       store/ (已提交)│   │                    │
                     └────────────────────────┘    └─────────────────────┘   └────────────────────┘
```

---

## 📁 目录结构说明

```
CamstarOntology/
├── .env.example                 # 环境变量模板文件
├── .gitignore                   # Git 忽略配置（已配置 data/vector_store 提交追踪）
├── requirements.txt             # 项目 Python 依赖声明
├── README.md                    # 本文档
├── AGENTS.md                    # 代理开发与开发流指南（含核心工作流及规范约束）
├── CLAUDE.md                    # IDE 指令快捷参考
├── run_all_builders.py          # [NEW] 一键重建与验证本地本体的辅助脚本
├── run_etl_full.py              # MES 业务数据全量/增量 ETL 装载管线
│
├── docs/                        # 物理数据库 Schema 与设计事实文档 (只读来源)
│   ├── Database_Tables.csv      # Camstar CDO（类名）物理表映射清单
│   ├── Database_Fields.csv      # CDO 字段、数据类型及物理外键关联定义
│   └── ontology_csv_validation_report.md  # 物理一致性自动校验结果报告
│
├── data/                        # 🗄️ 系统本地持久化数据层
│   └── vector_store/            # ChromaDB 向量数据库持久化目录（已包含预构建的向量索引数据）
│       ├── chroma.sqlite3       # 向量元数据 SQLite 文件
│       └── ...                  # 向量 HNSW 索引二进制文件
│
├── src/                         # 🐍 后端核心业务源码
│   ├── ontology/                # 本体定义与管理中心
│   │   ├── wiki_kb/             # 100+ 模块本体的原始定义数据
│   │   │   ├── *_ontology.json  # 模块本体的类、属性、关系声明
│   │   │   ├── *_modeling.md    # 中英文本体建模设计原理文档
│   │   │   ├── cross_module_ontology.json  # 跨模块拓扑关联定义汇总
│   │   │   └── product_lines.json  # 行业/产品线定义数据 (Semiconductor, Battery等)
│   │   ├── loader/
│   │   │   └── neo4j_loader.py  # JSON 本体 -> Neo4j 的 UNWIND 高效批量装载器
│   │   ├── runtime_state.py     # 空图谱/内置基线模式的持久化状态管理
│   │   └── wiki_manager.py      # 关系 Wiki 生成、读取与 product_lines 管理核心引擎
│   │
│   ├── qa/                      # RAG 问答与大模型交互引擎
│   │   ├── engine.py            # RAG 编排、ChromaDB 混合多路召回与对话处理
│   │   ├── graph_retriever.py   # Neo4j 拓扑子图抽取与关联路径检索器
│   │   ├── vectorizer.py        # PDF 文档解析、Overlap 切片与 ChromaDB 向量化构建器
│   │   ├── prompt_builder.py    # LLM 系统与用户 Prompt 模板组装器
│   │   └── logger.py            # 多轮对话审计日志记录器 (支持本地日期归档与查询)
│   │
│   └── etl/                     # 数据抽取与同步模块 (MES 生产数据到知识图谱)
│
├── scripts/                     # 🛠️ 运维与系统初始化脚本
│   ├── rebuild_indexes.py       # Neo4j 规范索引重建脚本 (包含 10 大全文/唯一约束索引)
│   ├── validate_ontology_vs_csv.py  # 物理一致性校验器，比对物理 CSV 结构与 JSON 本体定义
│   └── validate_relationship_sql.py # 全量校验 Relationship 的 Oracle / SQL Server 示例
│
└── web/                         # 🌐 前端 UI 与 API 宿主服务
    ├── server.py                # FastAPI 启动服务入口
    ├── shared.py                # Neo4j 驱动共享、ChromaDB 预热加载及模块类别着色配置
    └── routers/                 # API 业务模块化路由
    │   ├── graph.py             # G6 图谱拓扑、节点详情、统计信息 API
    │   ├── i18n.py              # 界面语言、节点及属性描述维护与 Designer 同步 API
    │   ├── ontology_import.py   # CSV 分析、业务对象审核导入和图谱清空 API
    │   ├── wiki.py              # Wiki Markdown 读写、单条/批量 AI Wiki 生成 API
    │   └── chat.py              # 问答助手 API 与多轮对话日志查询 API
    └── static/                  # 静态前端资源 (AntV G6 v5, Vanilla JS, CSS3)
        ├── index.html           # 本体图谱与对话主页面
        ├── industry.html        # 行业/产品线配置管理页面
        ├── logs.html            # 对话审计日志查看页面
        ├── app.js               # 图谱渲染、Combo 展开、差量动画及布局算法
        ├── chat.js              # 流式问答渲染、原生提及 (@Mention) 与节点跳转交互
        └── style.css            # 扁平蓝黑色工业质感 CSS 主题系统
```

---

## 🚀 快速开始与部署指南

对于新机器部署或者由于变更需要进行的数据迁移，可以使用以下指南快速恢复并运行整个平台。

### 1. 环境准备

确保目标机器已安装以下软件：

* **Python**: `≥ 3.10`（推荐 3.10 或 3.11）
* **Neo4j**: `≥ 5.x`（支持 Community/Enterprise 社区版及企业版均可）
* **支持 WebGL 的浏览器**: （推荐使用 Google Chrome, Microsoft Edge）

### 2. 获取源码与虚拟环境配置

```bash
# 克隆项目到本地
git clone https://github.com/yanghengde/CamstarOntology.git
cd CamstarOntology

# 创建 Python 虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux / macOS:
# source venv/bin/activate

# 升级 pip 并安装核心依赖项
pip install -r requirements.txt
```

### 3. 环境变量配置

复制并重命名配置文件：

```bash
copy .env.example .env       # Windows
# cp .env.example .env       # Linux / macOS
```

使用文本编辑器修改 `.env` 文件的值：

```ini
# Neo4j 图数据库连接地址及密码
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_secure_password

# DeepSeek API 密钥与端点配置 (用于问答与 Planner)
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat

# 图谱导入描述翻译（可选）
# auto：优先专用翻译 API，其次使用大模型；none：只显示英文原文
IMPORT_TRANSLATION_PROVIDER=auto
TRANSLATION_API_URL=
TRANSLATION_API_KEY=
```

Camstar Designer 描述同步会根据平台顶部选择的数据库类型连接数据源：SQL Server 使用 `SRC_DB_*`，Oracle 使用 `ORACLE_DB_*`。没有可用翻译服务时，结构分析和导入不会中断，中文界面会回退显示数据库中的英文描述。

> **CPU 依赖说明**：Linux 与 Windows 默认安装 CPU 版 PyTorch，运行平台不需要 CUDA 或 NVIDIA 驱动。`requirements.txt` 已固定官方 CPU wheel，避免 Docker 构建时下载 `nvidia-cuda-*` 依赖。

---

## 💾 数据库迁移与数据同步指南 (部署核心)

新部署一台机器时，如何将已有的**图数据库 (Neo4j)** 和**向量数据库 (ChromaDB)** 的数据完整同步过去？

### 💡 方案 A：直接克隆免配部署 (ChromaDB 本地向量库)

为简化部署流程，系统的 ChromaDB 向量数据库（存放有 Camstar 官方文档切片，大小约 15MB 左右）已经全部被追踪并提交到了 Git 仓库中，路径为：

* `data/vector_store/`

**新机器部署时：**

* 只要通过 `git clone` 拉取了最新代码，ChromaDB 就已经存在于你的本地。
* 在运行系统时，FastAPI 后端会在后台自动读取并装载 `data/vector_store/` 内的向量索引文件，**无需重新下载 Embedding 模型或重新向量化切片**，即可直接开始 Graph-RAG 对话。
* 如果后续需要重新构建向量库，可以运行以下命令从 PDF 重新构建：
  ```bash
  python src/qa/vectorizer.py
  ```

### 💡 方案 B：从本体 JSON 极速重构 Neo4j 数据

我们不需要像传统关系型数据库那样导出一个巨大的 SQL 备份。得益于本体定义的高度可读性和装载器强大的批量合并能力，你可以随时通过几条命令在新 Neo4j 数据库上重新生成所有的类、属性和关系边。

**执行步骤：**

1. **启动 Neo4j 服务**：确保新机器上的 Neo4j 服务已启动，且已根据 `.env` 配置好用户名和密码。
2. **校验本体文件规范性**（可选）：
   ```bash
   python scripts/validate_ontology_vs_csv.py
   ```

   这会比对 `docs/` 下的 CSV 表和物理字段，检查是否存在未对齐的类型或缺失的 Navigation 属性。

3. **校验全部 Relationship SQL 示例**（只读，不连接 Neo4j）：

   ```bash
   python scripts/validate_relationship_sql.py
   ```

   校验器会逐条核对本体关系与 `Database_Fields.csv` 的物理外键，并同时生成 Oracle、SQL Server 两种示例；任一关系无法唯一解析时会返回非零退出码。

4. **重建图数据库规范索引**：
   ```bash
   python scripts/rebuild_indexes.py
   ```

   *作用：在 Neo4j 中创建唯一性约束（如 `unique_ontology_class_name`、`unique_ontology_property`）以防脏数据生成，并创建全文索引以加速大模型的模糊检索。*
5. **批量 UNWIND 写入本体数据**：
   ```bash
   python src/ontology/loader/neo4j_loader.py
   ```

   *作用：解析 `src/ontology/wiki_kb/` 下的所有本体 JSON，通过 Cypher UNWIND 批量向 Neo4j 写入类、属性及关系。*

如果曾通过“图谱维护”执行一键清空，系统会将状态写入 `data/ontology_graph_state.json`，普通启动不会重新灌入内置本体。需要显式恢复内置 JSON 基线时执行：

```bash
python src/ontology/loader/neo4j_loader.py --force-baseline
```

---

## 🏃 启动 Web 系统

### Docker / Ubuntu 26.04

项目已提供 `Dockerfile` 和 `compose.yaml`，可一并运行 FastAPI、Neo4j、
本体自动初始化、Chroma 向量库、会话与日志持久化。完整迁移、备份和安全配置见
[`docs/docker_deployment_ubuntu.md`](docs/docker_deployment_ubuntu.md)。

```bash
docker compose build
docker compose up -d
docker compose ps
```

首次启动会把当前 `data/`、`logs/` 复制到 Docker 命名卷，并自动加载全部本体。图谱运行状态也保存在 `app_data` 命名卷中，因此空图谱模式可跨容器重启保持。

一切就绪后，通过以下命令启动 FastAPI 服务器：

```bash
python web/server.py
```

* 服务器将运行在 `http://localhost:5050` 上。
* 浏览器访问 `http://localhost:5050` 即可看到主页。
* 行业管理已整合进主页“平台设置 → 行业设置”；`/static/industry.html` 仅保留兼容访问。
* 访问 `http://localhost:5050/logs` 查看用户对话审计日志。

---

## 🎮 页面交互与功能使用指南

### 🌐 1. 本体知识图谱主页 (`index.html`)

* **拓扑大图渲染**：展示系统当前 593 个类节点和 1590 条关系边的全景。
* **查询构建器**：在主图中选择多个业务对象，系统会验证物理外键 Join 路径、展示关系预览并生成与顶部数据库类型一致的 Oracle 或 SQL Server 查询骨架。
* **统一适应操作**：顶部“适应”按钮用于将当前主图或查询聚焦结果重新适配到可视区域，保持与查询构建器中的操作风格一致。
* **邻域差量高亮**：点击任何节点（例如 `Container`），系统会在 **30ms 内**将该节点及其一阶邻边、邻近节点保持彩色高亮，将其余无关节点淡化置灰；右侧抽屉式详情面板会滑出，显示其物理 CDOName、中文名称、数据属性及入向/出向外键关联。
* **引用关系聚焦**：点击详情面板中的“它引用的对象”或“被何处引用”时，左侧详情切换到对应对象，主图只聚焦两个节点及连接线，不继续下钻其他邻居。
* **可拖拽详情面板**：节点详情面板可水平拖拽调整宽度，最大扩展到页面中线；超长内容使用省略号显示，鼠标悬停可查看完整文本。
* **关系阅读增强**：Relationship 用法阅读区支持更大的可滚动区域；SQL 关联示例默认展开、可折叠，并提供一键复制按钮。

### 💬 2. RAG 智能对话侧栏 (流式 + @提及)

* 在图谱右侧的问答面板输入您想了解的问题，如：`什么是 WIPMessageDefMgr 并在制品是如何挂起的？`
* 键入 `@` 字符会激活图谱实体的模糊联想菜单，选中后双括号包裹（如 `[[Container]]`），大模型会针对该实体相关的邻域知识开展精准回答。
* **智能高亮跳转**：AI 回答中的实体名会在前端自动转换成蓝色链接。点击链接，图谱会自动平滑移动视口（Focus & Pan To）到目标节点并触发高亮，实现“看图问答，问答触图”的双向交互。

### ⚙️ 3. 平台设置

点击主页右上角齿轮按钮进入平台设置，左侧包含五个独立菜单：

1. **语言与显示**：切换中文/英文界面，当前页面即时生效。
2. **节点与属性描述**：搜索并选择节点，维护节点描述以及该节点下每个属性的中英文描述；属性技术字段名不会被翻译或修改。点击“同步当前节点”可从顶部所选的 Oracle 或 SQL Server Camstar Designer 数据源获取描述。
3. **图谱导入**：上传 `Database_Tables.csv` 与 `Database_Fields.csv`，分析 CDO、属性和物理外键。已审核节点默认选中，新 CDO 必须人工确认，规则/配置/历史明细类对象不会被无条件批量导入。
4. **图谱维护**：提供独立的一键清空入口。系统会先读取并展示当前 Neo4j 规模，只有勾选不可撤销确认并输入指定确认词后才能执行。
5. **行业设置**：在当前设置弹窗内新建或编辑行业/产品线，并生成关系建模提示词。

描述保存和界面语言切换均为热更新，所有已打开页面会自动获取最新配置，无需重启服务。

### 🏭 4. 行业/产品线配置管理

* 用户可在“平台设置 → 行业设置”中定义不同的产品线/行业参数（如行业代号、名称、描述、主题颜色、显示图标）。
* 切换页面顶部的行业（如“半导体”或“新能源”），主页图谱及各子页面的所有请求都将附带 `?industry=industry_id` 参数。

---

## 📝 完整 REST API 接口定义

FastAPI 后端网关按图谱、关系 Wiki、问答、国际化与受审核导入划分路由组，以下为主要接口：

### 📁 1. 图谱拓扑接口 (`web/routers/graph.py`)

#### `GET /api/graph/overview`

* **功能**：获取全量图谱的节点、连线与 Combo 划分（仅传输核心元数据，传输性能优秀）。
* **响应格式**：
  ```json
  {
    "nodes": [
      { "id": "Container", "data": { "label": "Container", "chineseName": "容器", "layer": "Execution", "module": "container" } }
    ],
    "edges": [
      { "source": "Container", "target": "Spec", "data": { "label": "Spec", "cardinality": "0..1" } }
    ],
    "combos": [
      { "id": "container", "data": { "label": "Container" } }
    ]
  }
  ```

#### `GET /api/graph/class/{class_name}`

* **功能**：查询特定类节点的详细属性定义、入向和出向关联边（支持 `Cache-Control` 强缓存以提升性能）。
* **响应格式**：
  ```json
  {
    "className": "Container",
    "properties": [
      { "name": "isFrozen", "dataType": "Boolean", "description": "是否冻结" }
    ],
    "outgoing": [
      { "targetClass": "QtyDef", "relName": "uOM", "cardinality": "0..1", "description": "单位定义" }
    ],
    "incoming": []
  }
  ```

#### `GET /api/stats`

* **功能**：返回 Neo4j 中已加载的类节点总数、属性总数和关系边总数。

#### `GET /api/product-lines`

* **功能**：返回已注册的产品线/行业列表（例如：`general`、`semiconductor`、`battery` 等）。

#### `POST /api/product-lines`

* **功能**：更新或保存产品线配置文件 `product_lines.json`。

---

### 📖 2. 关系 Wiki 接口 (`web/routers/wiki.py`)

#### `GET /api/wiki/relationship`

* **功能**：读取两个实体类在特定关系边上的 Wiki 建模说明书（Markdown 格式）。
* **参数**：`source` (源类名), `rel` (关系名), `target` (目标类名), `product_line` (行业ID)

#### `POST /api/wiki/save`

* **功能**：手动修改并保存一条特定关系的 Wiki 内容。

#### `POST /api/wiki/generate-one`

* **功能**：针对某一特定关系，调用 DeepSeek 流式生成一份高质量的中英文双语建模说明书。

#### `POST /api/wiki/generate-batch`

* **功能**：启动后台任务，一键流式为图谱中所有缺失 Wiki 的关系批量进行 AI 生成，前端支持实时进度百分比及 skips/failures 计数器渲染。

---

### 🤖 3. Graph-RAG 流式问答接口 (`web/routers/chat.py`)

#### `POST /api/chat`

* **功能**：发送用户问题，开展基于图谱邻域提取的 RAG 智能流式问答。
* **参数**：
  ```json
  {
    "question": "用户输入的具体提问",
    "session_id": "可选的会话ID (用于多轮对话历史管理)",
    "product_line": "行业ID (如 battery)"
  }
  ```
* **返回**：`text/event-stream` SSE 流。结束时会返回提取到的图元关键词、提取到的类链接（以供高亮渲染）和审计 `trace_id`。

#### `POST /api/chat/clear`

* **功能**：清除特定 `session_id` 的多轮对话历史上下文。

#### `GET /api/logs`

* **功能**：查询与审计用户的多轮对话记录。支持按日期、会话 ID、关键字过滤。

---

### 🌐 4. 语言与描述接口 (`web/routers/i18n.py`)

#### `GET /api/i18n`

* **功能**：读取当前界面语言版本、节点描述和属性描述翻译配置。

#### `GET /api/i18n/catalog`

* **功能**：从当前 Neo4j 图谱搜索可维护的节点；支持分页，不会展示已经清空或尚未导入的 JSON 节点。

#### `GET /api/i18n/node/{class_name}`

* **功能**：返回指定节点及其实际属性列表，用于编辑节点描述和属性描述。属性字段技术原名保持不变。

#### `PUT /api/i18n/translation`

* **功能**：保存单个节点描述或属性描述的中英文内容，并通过版本轮询热更新到已打开页面。

#### `POST /api/i18n/sync-descriptions`

* **功能**：根据请求中的 `oracle` 或 `sqlserver` 数据库类型，从 Camstar Designer CDO 元数据同步节点与属性英文描述，并在翻译服务可用时补充中文描述。

---

### 📥 5. 图谱导入与维护接口 (`web/routers/ontology_import.py`)

#### `POST /api/ontology-import/analyze`

* **功能**：上传表定义和字段定义 CSV，分析候选 CDO、属性与物理外键关系。
* **安全策略**：当前图谱中的节点被视为已审核业务对象；新 CDO 默认不选中，必须由用户确认业务意义。

#### `GET /api/ontology-import/translation/{import_id}`

* **功能**：查询 Designer 描述读取和后台中文翻译进度。

#### `POST /api/ontology-import/apply`

* **功能**：只将本次明确选中的业务对象、所属属性及选中范围内的物理关系增量写入 Neo4j。

#### `GET /api/ontology-import/clear-preview`

* **功能**：只读统计当前数据库将受清空操作影响的类、属性、关系及全部 Neo4j 节点数量。

#### `POST /api/ontology-import/clear`

* **功能**：清空当前配置的 Neo4j 数据库并启用持久化空图谱模式。
* **重要警告**：这是不可撤销操作。后端要求 `acknowledgeIrreversible=true`，并校验完整确认词；前端同时提供独立危险操作页面和二次确认。该操作不会删除物理 CSV、描述翻译、行业配置或仓库内的本体 JSON。

---

## 🛡️ 系统安全性与版权申明

* **内部交流**：本项目仅限企业内部技术方案验证、MES 蓝图建模与学术性研究使用。
* **商标声明**：`Siemens`、`Opcenter`、`Camstar` 为西门子股份公司 (Siemens AG) 及其子公司的注册商标。本平台所体现的类名、字段及关联网络纯属对物理出厂表结构的本体化映射呈现。
