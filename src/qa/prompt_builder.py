"""
Step 3: Prompt Builder
──────────────────────
Merges graph context + vector context + conversation history
into a compact prompt for DeepSeek.
"""

import os

def build_prompt(
    question: str,
    graph_context: str,
    vector_context: str,
    history: list[dict] | None = None,
    product_line: str = "general",
    assistant_mode: str = "sql",
    sql_schema_context: str = "",
    sql_domain_context: str = "",
    sql_query_plan_context: str = "",
    known_classes: list[str] | None = None,
    sql_dialect: str = "oracle",
) -> list[dict]:
    """
    Build the complete message list for the LLM API call.
    Uses compact context to reduce token count and latency.
    """
    if assistant_mode == "sql":
        dialect = (sql_dialect or "oracle").lower()
        if dialect not in {"oracle", "sqlserver"}:
            dialect = "oracle"
        if dialect == "sqlserver":
            dialect_name = "SQL Server"
            pagination_rule = (
                "4. 明细查询默认使用 `SELECT TOP (100)`，除非用户明确指定数量；不要 SELECT *，只选择需要的列。"
                "禁止使用 Oracle 的 FETCH FIRST、ROWNUM、NVL、SYSDATE 等语法。\n"
            )
            parameter_rule = (
                "5. 表名和字段名按物理架构原样输出并使用清晰别名；所有筛选值必须使用 SQL Server "
                "`@参数名`，即使用户给出了数字或文本值也不能直接写入 SQL 字面量。\n"
            )
        else:
            dialect_name = "Oracle"
            pagination_rule = (
                "4. 明细查询默认使用 `FETCH FIRST 100 ROWS ONLY`，除非用户明确指定数量；不要 SELECT *，只选择需要的列。"
                "禁止使用 SQL Server 的 TOP、方括号标识符、GETDATE、ISNULL 等语法。\n"
            )
            parameter_rule = (
                "5. 表名和字段名按物理架构原样输出并使用清晰别名；所有筛选值必须使用 Oracle `:参数名`，"
                "即使用户给出了数字或文本值也不能直接写入 SQL 字面量。\n"
            )
        system_prompt = (
            "你是 Siemens Opcenter Execution（Camstar）只读 SQL 助手，服务对象是需要查询后台业务数据的 IT 人员。"
            f"当前数据库方言为 {dialect_name} SQL，所有 SQL 必须严格使用该方言。\n\n"
            "强制规则：\n"
            "1. 表名、字段名、主键和外键连接条件只能使用“物理数据库架构”中明确出现的内容；"
            "本体 camelCase 属性不能直接当作物理列名。不得猜测任何表或列。SQL、说明和注意事项中都不得"
            "推荐、暗示或举例引用物理上下文之外的表和字段。\n"
            "2. JOIN 必须优先使用上下文明确给出的 FK→目标表.目标字段；没有连接证据时说明缺少依据，"
            "不要用同名字段臆造连接。\n"
            "3. 只生成只读 SELECT 或以 SELECT 结束的 CTE。拒绝生成或改写 INSERT、UPDATE、DELETE、"
            "MERGE、TRUNCATE、DROP、ALTER、CREATE、EXEC 等会修改数据或结构的语句。\n"
            f"{pagination_rule}"
            f"{parameter_rule}"
            "6. 若需求、时间范围、状态含义或目标表不明确，先给可确认的查询骨架，并明确标出待确认参数；"
            "不得把不确定业务含义说成事实。不得根据 DataTypeCode 猜测业务枚举值，也不得虚构状态值说明。\n"
            "7. 输出固定包含：`### SQL`（sql代码块）、`### 说明`、`### 使用的表与连接`、`### 注意事项`。"
            "提及图谱类名时使用 [[ClassName]]，便于界面定位。\n"
            "8. SQL 仅供生成、审核和复制；本系统不连接业务数据库，也不执行 SQL。"
            "9. 输出前逐一自检 SQL 和说明中的表名、字段名；删除所有物理上下文中不存在的对象。"
            "不要主动推荐其他表、事务接口或后续扩展查询。"
            "10. 当用户请求写操作时只简短拒绝，不自动改写成 SELECT，也不提供任何替代修改方案。\n"
            "11. 若提供了“结构化查询计划”，必须严格遵循其中已确认的对象、指标、粒度、时间范围和时间字段。"
            "日期范围必须使用参数化半开区间（时间字段 >= 开始参数 AND 时间字段 < 结束参数），"
            "禁止对时间字段使用 TRUNC、CAST 或 CONVERT 后再比较，以免索引失效或改变时间口径。"
        )
    else:
        show_cn_alias = os.getenv("SHOW_CN_ALIAS", "false").lower() == "true"

        if show_cn_alias:
            system_prompt = (
                "你是 Opcenter EX CR 建模助手。基于给定上下文用中文简洁回答。\n\n"
                "规则：\n"
                "1. 只基于上下文，不编造。提及本体类名用[[英文类名]]（中文名称）标记。\n"
                "2. 多对象用表格，步骤用编号。上下文不足时说明。"
            )
        else:
            system_prompt = (
                "你是 Opcenter EX CR 建模助手。基于给定上下文用中文简洁回答。\n\n"
                "规则：只基于上下文，不编造；提及本体类名用[[英文类名]]标记。"
            )

    if product_line and product_line != "general":
        try:
            from src.ontology.wiki_manager import get_product_line_info
            pl = get_product_line_info(product_line)
            if pl and pl.get("name"):
                system_prompt += f"\n当前行业/产品线: {pl['name']}。请结合该行业/产品线（描述: {pl.get('description', '')}）的特定背景、流程和术语来回答。"
        except Exception:
            pass

    messages = [{"role": "system", "content": system_prompt}]

    # SQL follow-ups need the last accepted query, not a large pile of prior
    # model prose. Historical invalid SQL is excluded from future prompts.
    if history:
        retained = []
        retained_chars = 0
        retained_user_turns = 0
        retained_sql_answers = 0
        inspected_latest_assistant = False
        for turn in reversed(history[-40:]):
            content = turn.get("content") or ""
            if not content:
                continue
            role = turn.get("role")
            if assistant_mode == "sql":
                if role == "user":
                    if retained_user_turns >= 3:
                        continue
                    retained_user_turns += 1
                elif role == "assistant":
                    if inspected_latest_assistant:
                        continue
                    inspected_latest_assistant = True
                    from src.qa.sql_validator import validate_sql_answer
                    validation = validate_sql_answer(
                        content,
                        dialect=sql_dialect,
                    )
                    if not validation.valid or not validation.sql:
                        continue
                    retained_sql_answers += 1
                else:
                    continue
                budget = 10000
            else:
                budget = 24000
            if retained and retained_chars + len(content) > budget:
                break
            retained.append(turn)
            retained_chars += len(content)
        for turn in reversed(retained):
            clean_turn = {
                "role": turn.get("role"),
                "content": turn.get("content")
            }
            if clean_turn.get("role") and clean_turn.get("content"):
                messages.append(clean_turn)

    # Build user message with compact context
    parts = []
    if assistant_mode == "sql" and known_classes:
        known_list = "、".join(f"[[{name}]]" for name in known_classes)
        parts.append(
            "## 用户明确指定的已知对象（优先约束）\n"
            f"{known_list}\n"
            "生成 SQL、选择表及推理 JOIN 路径时必须优先考虑这些对象。"
            "能用物理外键连通时给出经过验证的连接；无法连通时明确说明缺少连接证据，"
            "不得为了全部使用而臆造 JOIN。"
        )
    if assistant_mode == "sql" and sql_query_plan_context:
        parts.append(
            "## 结构化查询计划（已确认意图，生成时必须遵循）\n"
            f"{sql_query_plan_context}"
        )
    if assistant_mode == "sql" and sql_schema_context:
        parts.append(f"## 物理数据库架构（唯一SQL事实来源）\n{sql_schema_context}")
    if assistant_mode == "sql" and sql_domain_context:
        parts.append(f"## SQL领域口径（用于选表与防止误统计）\n{sql_domain_context}")
    if graph_context:
        parts.append(f"## 业务语义与关系图谱（辅助理解，不能替代物理字段）\n{graph_context}")
    if vector_context and vector_context != "未配置向量检索。":
        parts.append(f"## 文档\n{vector_context}")
    parts.append(f"## 问题\n{question}")

    user_msg = "\n\n".join(parts)
    messages.append({"role": "user", "content": user_msg})

    return messages


def format_vector_results(results: dict) -> str:
    """Format ChromaDB query results into compact context."""
    if not results or not results.get("documents"):
        return "未找到相关文档片段。"

    lines = []
    docs = results["documents"][0] if results["documents"] else []
    metas = results["metadatas"][0] if results["metadatas"] else []

    for i, (doc, meta) in enumerate(zip(docs, metas)):
        chapter = meta.get("chapter", "Unknown")
        page = meta.get("start_page", "?")
        # Tighter truncation: 250 chars per chunk
        text = doc[:250] + "..." if len(doc) > 250 else doc
        lines.append(f"**[{chapter}, P.{page}]**\n{text}")

    return "\n\n".join(lines) if lines else "未找到相关文档片段。"
