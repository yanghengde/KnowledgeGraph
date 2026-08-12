# Camstar Ontology: 图谱驱动的智能问答与可视化高亮架构设计 (Graph-RAG Subgraph Highlighting V2.0)

## 1. 核心业务愿景
随着 Camstar Ontology 的本体对象扩展到 15 个模块，对象间的业务逻辑已经形成了高度交织的网络。当用户通过自然语言发起复杂的跨模块追踪问题（例如：“*工作流是如何跟底层物料发生关联的？*”）时，系统不仅应输出结构化的文本解答，还需要具备**“所问即所指”**的能力：即时在左侧全局知识图谱中，**抽取并高亮出那条隐形的业务血脉链路**。这将极大增强基于 RAG 问答的透明度、可信度与震撼的用户体验。

---

## 2. 系统分层架构与职责划分 (Separation of Concerns)

为了保证这一核心版本的健壮性与可扩展性，我们将采用严格的分层架构设计：

### 层级 1：Agent 意图与路由层 (Intent & Routing Layer)
- **核心逻辑**：采用 LangChain / LlamaIndex 代理机制。
- **职责**：
  1. 拦截用户问题，判断是**普通语义问答**还是**图谱链路探索**。
  2. 提取问题中的核心实体（Entity Extraction），如“工作流”、“物料”。
  3. 通过 Fuzzy Matching 确保提取到的词汇精准匹配 Neo4j 库中的 `OntologyClass` 名称（防止大模型幻觉输出不存在的类名）。

### 层级 2：动态图查询层 (Dynamic Graph Query Layer)
- **核心逻辑**：图寻路算法 (Pathfinding Tool) 与 Cypher 执行器。
- **职责**：
  1. 向大模型暴露一个专属工具 `OntologyPathFinderTool`。
  2. 根据起点和终点实体，执行可控深度的图路径搜索。
  3. **防御机制**：限制最大跳数（如 `[*1..5]`），避免笛卡尔积爆炸造成数据库 OOM。
  > 示例核心 Cypher：
  > `MATCH path=shortestPath((start:OntologyClass {name:$start_entity})-[*1..5]-(end:OntologyClass {name:$end_entity})) RETURN path`

### 层级 3：双轨数据聚合层 (Dual-Payload Aggregation Layer)
- **核心逻辑**：Python 后端接口层打包逻辑。
- **职责**：
  1. 将查询到的 `path` 拓扑数据投喂给 LLM，让其生成对用户友好的自然语言解答。
  2. 深度解析 Neo4j 返回的 `path` 游标，严格拆离出 `nodes` (包含哪些类) 和 `edges` (关系链路类型)。
  3. **数据清洗**：剔除重复节点，组装标准化 JSON Contract，返回给前端。

### 层级 4：前端交互渲染层 (UI Render & State Machine)
- **核心逻辑**：AntV G6 的状态机与动画。
- **职责**：
  1. 解析来自后端的独立 `highlight` 载荷。
  2. 执行精确的图元状态翻转（State Reversal）。
  3. 控制摄像机视口（Viewport）进行动态聚焦。

---

## 3. 标准数据契约接口设计 (API Data Contract)

前后端需要遵循严格的 JSON 契约以实现通用化解耦。无论未来后台图谱多复杂，前端只负责渲染。

```json
{
  "status": "success",
  "data": {
    "answer": "在 Camstar 系统中，工作流 (Workflow) 通过包含特定工序 (Operation)，而产品 (Product) 设定了默认的工作流，同时产品向下关联了 BOM (物料清单)...",
    "graph_context": {
      "is_path_found": true,
      "highlight": {
        "nodes": ["Workflow", "Operation", "Product", "BOM", "Material"],
        "edges": ["HAS_BOM", "USES_DEFAULT_WORKFLOW", "USES_OPERATION", "CONSUMES_MATERIAL"]
      }
    }
  }
}
```
*注：如果意图层判定无需高亮，或 `is_path_found` 为 false，则 `highlight` 字段为空，前端保持默认原图。*

---

## 4. 严密的异常处理与降级策略 (Robustness & Fallback)

在企业级架构中，必须考虑到大模型与图查询可能出现的边缘情况：

1. **实体未识别或拼写错误**：
   - 降级策略：如果在本体库中找不到对应的起点/终点类名，不执行 Cypher，跳过高亮逻辑，降级为纯文本向量库搜索回答。
2. **图中不存在通路 (No Path)**：
   - 如果起点和终点在当前图谱（如 15 个模块）中物理上处于孤岛，查询返回为空。
   - 降级策略：在 `graph_context` 中标记 `is_path_found: false`，大模型会在文本中回答：“根据目前的系统架构，X与Y之间不存在直接的数据联系。”
3. **查询链路过长或发散**：
   - 降级策略：在后端图查询引擎中强制植入阈值拦截，例如超过 50 个节点或边的高亮请求将被强制截断，以防前端 G6 渲染崩溃或失去高亮焦点意义。

---

## 5. 前端状态机演进 (State Machine Details)

前端图谱（G6）将引入严格的交互状态机：

- **状态 A: 默认全景图 (Default)**
  - 所有节点/边按各自模块配色正常渲染，透明度 1.0。
- **状态 B: 高亮暗化态 (Dimmed & Focus)**
  - 当接收到 QA 返回的 `highlight` 信号时触发。
  - 全局降维：所有未在 `highlight.nodes/edges` 数组内的图元，`opacity` 渐变至 `0.15`，去除阴影。
  - 核心发光：被选中的节点保留原本配色，`lineWidth` 加粗至 4，加上强烈的发光特效（Glow Shadow）。
  - 镜头锁定：触发 `graph.fitView()` 并限制最大 Zoom 级别，将高亮路径稳稳放在视野中心。
- **状态 C: 重置态 (Reset)**
  - 当用户点击画板空白处（`canvas:click`），或是开启新一轮普通问答时。
  - 状态重置机制清空所有内部 flag，平滑过渡回到状态 A。

---

## 6. 核心优势总结
这份设计跳出了传统“硬编码高亮”的桎梏，实现了**图谱寻路与交互表现的完全解耦**。
通过**“大模型意图 -> Cypher 路径 -> 节点/边坐标抽象 -> 前端盲打高亮”**的流水线，无论您未来继续在 Ontology 里面增加多达 100 个领域，这套 RAG 高亮逻辑均**不需要修改哪怕一行代码**，具备极强的生命力与拓展性。
