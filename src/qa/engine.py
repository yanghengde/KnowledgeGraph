"""
QA Engine – Orchestrates Graph + Vector hybrid RAG
──────────────────────────────────────────────────
1. Extract entities from the user question (via keyword matching + LLM)
2. Parallel retrieval: Neo4j graph + ChromaDB vector
3. Assemble prompt with conversation history
4. Stream response from DeepSeek
"""
import os
import re
import json
from openai import OpenAI
from dotenv import load_dotenv
from src.qa.graph_retriever import search_graph, format_graph_context, get_all_class_names
from src.qa.prompt_builder import build_prompt, format_vector_results
from src.qa.sql_entity_resolver import resolve_sql_entities
from src.qa.logger import ChatTrace, CHAT_LOG_ENABLED
import glob

# Dynamically loaded Chinese to English class name mappings
CN_MAP = {}

def _load_cn_map():
    global CN_MAP
    CN_MAP.clear()
    
    CN_MAP.update({
        "工艺路线": "Workflow", "流程": "Workflow",
        "步骤": "WorkflowStep", "工段": "Operation",
        "规范": "Spec", "指令": "Spec", "rework": "Rework",
        "物料": "Product", "设备": "ResourceDef", "资源": "ResourceDef",
        "任务列表": "TaskList", "批次": "Container",
        "工单": "MfgOrder", "在制品": "Container",
        "警报": "AlarmDef", "挂起": "HoldReason",
        "工作中心": "WorkCenter", 
        "派工": "DispatchRule", "排程": "DispatchRule",
        "认证": "Skill", "资质": "Skill",
        "保养": "Resource", "校准": "Resource",
        "集团": "Enterprise", "园区": "Site", "车间": "Factory", "厂房": "Factory",
        "洁净室": "ManufacturingArea", "区域": "ManufacturingArea",
        "生产线": "ProductionLine", "排班": "ShiftPattern", "轮班": "ShiftPattern",
        "在制品消息": "WipMessage",
    })
    
    # Dynamically extract chineseName from ontology JSONs to auto-map new objects
    kb_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ontology", "wiki_kb")
    for file_path in glob.glob(os.path.join(kb_path, "*_ontology.json")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for cls in data.get("classes", []):
                    cname = cls.get("chineseName")
                    ename = cls.get("className")
                    if cname and ename:
                        CN_MAP[cname] = ename
        except Exception as e:
            print(f"Error loading {file_path} for CN_MAP: {e}")

_load_cn_map()

load_dotenv(override=True)

# DeepSeek client
_llm_client = None
_async_llm_client = None
_class_names = None

UNSAFE_SQL_REQUEST = re.compile(
    r"\b(INSERT|UPDATE|DELETE|MERGE|TRUNCATE|DROP|ALTER|CREATE|EXEC(?:UTE)?)\b"
    r"|(?:帮我|请|给我|写|生成|执行|直接|需要|想要).{0,20}"
    r"(?:删除|删掉|清空|更新|修改|写入|插入|新增|建表|删表)"
    r"|(?:删除|删掉|清空|更新|修改|写入|插入|新增|建表|删表).{0,12}(?:SQL|语句)"
    r"|^\s*(?:删除|删掉|清空|更新|修改|写入|插入|新增|建表|删表)",
    re.IGNORECASE,
)


def _get_llm():
    global _llm_client
    if _llm_client is None:
        _llm_client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            timeout=float(os.getenv("LLM_TIMEOUT", "120")),
        )
    return _llm_client


def _get_async_llm():
    global _async_llm_client
    if _async_llm_client is None:
        from openai import AsyncOpenAI
        _async_llm_client = AsyncOpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            timeout=float(os.getenv("LLM_TIMEOUT", "120")),
        )
    return _async_llm_client


def _get_class_names():
    global _class_names
    if _class_names is None:
        _class_names = get_all_class_names()
    return _class_names


def extract_keywords(question: str, fallback: bool = True) -> list[str]:
    """
    Extract relevant ontology keywords from the user question.
    Uses a two-pronged approach:
      1. Direct matching against known class names
      2. Chinese keyword heuristics
    """
    # ``fallback`` is retained for API compatibility, but intentionally no
    # longer injects Workflow for unrelated questions.
    from src.qa.sql_schema_retriever import _schema
    physical_tables, _ = _schema()
    sql_objects = list(dict.fromkeys(
        _get_class_names() + list(physical_tables)
    ))
    return resolve_sql_entities(question, sql_objects, CN_MAP)


async def query(
    question: str,
    history: list[dict] | None = None,
    vector_collection=None,
    product_line: str = "general",
    assistant_mode: str = "sql",
    selected_classes: list[str] | None = None,
    known_classes: list[str] | None = None,
    sql_dialect: str = "oracle",
    query_plan: dict | None = None,
) -> str:
    """
    Non-streaming query: returns complete answer string.
    """
    chunks = []
    async for chunk in query_stream(
        question,
        history,
        vector_collection,
        product_line=product_line,
        assistant_mode=assistant_mode,
        selected_classes=selected_classes,
        known_classes=known_classes,
        sql_dialect=sql_dialect,
        query_plan=query_plan,
    ):
        if isinstance(chunk, str):
            chunks.append(chunk)
    return "".join(chunks)


async def query_stream(
    question: str,
    history: list[dict] | None = None,
    vector_collection=None,
    trace: ChatTrace | None = None,
    product_line: str = "general",
    assistant_mode: str = "sql",
    selected_classes: list[str] | None = None,
    known_classes: list[str] | None = None,
    sql_dialect: str = "oracle",
    query_plan: dict | None = None,
):
    """
    Streaming query: yields answer chunks as they arrive from DeepSeek.
    Pure Graph RAG strategy: Graph + Vector + LLM streaming.
    If 'trace' is provided, each step's timing and metadata are logged.
    """
    if assistant_mode == "sql" and UNSAFE_SQL_REQUEST.search(question):
        yield (
            "### 安全限制\n"
            "Camstar SQL 助手只生成只读 `SELECT` 或以 `SELECT` 结束的 CTE，"
            "不提供 `INSERT`、`UPDATE`、`DELETE`、`MERGE`、DDL 或存储过程执行语句。"
            "该请求未执行，也未生成修改数据的替代语句。"
        )
        return

    # 1. Extract entities/keywords
    step_kw = trace.add_step("关键词提取") if trace else None
    selected_classes = selected_classes or []
    known_classes = known_classes or []
    keywords = list(
        dict.fromkeys(
            extract_keywords(
                question,
                fallback=False,
            )
            + known_classes
            + selected_classes
        )
    )
    if step_kw:
        step_kw.done(output={"keywords": keywords})

    if assistant_mode == "sql" and not keywords:
        yield (
            "### 需要确认查询对象\n"
            "我还无法从当前问题中确定要查询的物理业务对象。"
            "请从左侧加入一个对象，或在问题中使用 `@表名`，"
            "例如 `@Container`、`@MfgOrder` 或 `@HistoryMainline`。"
        )
        return

    # Reviewed semantic metrics bypass free-form LLM SQL generation. The
    # contract fixes the fact table, measure, grain and physical JOINs.
    metric_id = (query_plan or {}).get("metric_id")
    if assistant_mode == "sql" and metric_id:
        from src.qa.semantic.example_index import resolve_static_sql_example
        from src.qa.semantic.metric_catalog import get_metric
        from src.qa.semantic.metric_validator import validate_metric_sql
        from src.qa.semantic.sql_renderer import render_static_metric_answer
        from src.qa.sql_query_planner import format_query_plan_markdown
        from src.qa.sql_validator import validate_sql_answer

        step_metric = trace.add_step("指标语义层") if trace else None
        metric_contract = get_metric(metric_id)
        try:
            effective_question = (
                query_plan.get("effective_question") or question
            )
            static_example = resolve_static_sql_example(
                effective_question,
                dialect=sql_dialect,
                metric_id=metric_id,
                time_scope=query_plan.get("time_scope"),
                time_basis=query_plan.get("time_basis"),
            )
            if not static_example:
                yield {
                    "type": "status",
                    "content": (
                        f"已识别指标合同 {metric_id}，"
                        "但未命中固定 SQL 模板。"
                    ),
                }
                full_answer = (
                    f"{format_query_plan_markdown(query_plan)}\n\n"
                    "### 未命中标准 SQL 模板\n\n"
                    "当前问题与语义模板库中的标准问题距离不足，"
                    "因此没有返回或临时生成 SQL。请换用更接近的标准问法，"
                    "或先将该问法及审核后的 SQL 加入模板库。"
                )
                yield full_answer
                if step_metric:
                    step_metric.done(output={
                        "metric_id": metric_id,
                        "fact_table": metric_contract["factTable"],
                        "contract_status": metric_contract.get("status"),
                        "sql_valid": False,
                        "llm_bypassed": True,
                        "sql_source": None,
                        "semantic_example_id": None,
                        "template_matched": False,
                    })
                return

            yield {
                "type": "status",
                "content": (
                    f"已命中标准问题 {static_example['case_id']}，"
                    "正在读取不可变 Golden SQL…"
                ),
            }
            body = render_static_metric_answer(
                metric_contract,
                sql=static_example["golden_sql"],
                example_id=static_example["case_id"],
                distance=static_example["distance"],
            )
            physical_validation = validate_sql_answer(
                body,
                dialect=sql_dialect,
                query_plan=query_plan,
            )
            metric_validation = validate_metric_sql(
                body,
                metric_contract,
                time_basis=query_plan.get("time_basis"),
            )
            if physical_validation.valid and metric_validation.valid:
                full_answer = (
                    f"{format_query_plan_markdown(query_plan)}\n\n{body}"
                )
                yield full_answer
                if step_metric:
                    step_metric.done(output={
                        "metric_id": metric_id,
                        "fact_table": metric_contract["factTable"],
                        "contract_status": metric_contract.get("status"),
                        "sql_valid": True,
                        "llm_bypassed": True,
                        "sql_source": (
                            "immutable_golden_sql"
                        ),
                        "semantic_example_id": static_example.get("case_id"),
                        "template_matched": True,
                    })
            else:
                errors = (
                    physical_validation.errors + metric_validation.errors
                )
                full_answer = (
                    f"{format_query_plan_markdown(query_plan)}\n\n"
                    "### 指标 SQL 校验未通过\n\n"
                    "指标合同生成结果未通过确定性校验，因此没有返回候选 SQL。\n\n"
                    + "\n".join(f"- {error}" for error in errors)
                )
                yield full_answer
                if step_metric:
                    step_metric.fail("; ".join(errors))
            return
        except Exception as exc:
            if step_metric:
                step_metric.fail(str(exc))
            yield (
                "### 指标 SQL 生成失败\n\n"
                f"指标合同 `{metric_id}` 无法生成安全SQL：{exc}"
            )
            return

    # 2. Graph retrieval
    step_graph = trace.add_step("图谱检索") if trace else None
    ontology_names = set(_get_class_names())
    graph_keywords = [
        keyword for keyword in keywords if keyword in ontology_names
    ]
    graph_data = search_graph(graph_keywords)
    graph_context = format_graph_context(graph_data)
    if step_graph:
        step_graph.done(output={
            "matched_classes": len(graph_data.get("matched_classes", [])),
            "relationships": len(graph_data.get("relationships", [])),
            "properties": len(graph_data.get("properties", [])),
        })

    # 3. Vector retrieval (supplementary context)
    step_vec = trace.add_step("向量检索") if trace else None
    vector_context = "未配置向量检索。"
    if assistant_mode == "sql":
        vector_context = "SQL模式仅使用物理数据库架构与本体关系。"
        if step_vec:
            step_vec.done(output={"chunks_retrieved": 0, "skipped_for_sql": True})
    elif vector_collection is not None:
        try:
            results = vector_collection.query(
                query_texts=[question],
                n_results=3,
            )
            vector_context = format_vector_results(results)
            if step_vec:
                chunks_count = len(results.get("documents", [[]])[0]) if results.get("documents") else 0
                step_vec.done(output={"chunks_retrieved": chunks_count})
        except Exception as e:
            vector_context = f"向量检索错误: {e}"
            if step_vec:
                step_vec.fail(str(e))
    else:
        if step_vec:
            step_vec.done(output={"chunks_retrieved": 0})

    # 4. Build prompt
    step_prompt = trace.add_step("提示词构建") if trace else None
    sql_schema_context = ""
    sql_domain_context = ""
    sql_query_plan_context = ""
    planning_question = question
    if assistant_mode == "sql":
        from src.qa.sql_schema_retriever import build_sql_schema_context
        from src.qa.sql_domain_context import build_sql_domain_context
        from src.qa.sql_query_planner import (
            SqlQueryPlan,
            format_query_plan_context,
        )

        plan_value = SqlQueryPlan.from_dict(query_plan)
        if plan_value:
            planning_question = plan_value.effective_question or question
            sql_query_plan_context = format_query_plan_context(plan_value)
        sql_schema_context = build_sql_schema_context(
            keywords,
            question=planning_question,
        )
        sql_domain_context = build_sql_domain_context(
            keywords,
            question=planning_question,
        )
    messages = build_prompt(
        planning_question,
        graph_context,
        vector_context,
        history,
        product_line=product_line,
        assistant_mode=assistant_mode,
        sql_schema_context=sql_schema_context,
        sql_domain_context=sql_domain_context,
        sql_query_plan_context=sql_query_plan_context,
        known_classes=known_classes,
        sql_dialect=sql_dialect,
    )
    if step_prompt:
        step_prompt.done(output={
            "system_tokens": len(messages[0]["content"]) // 3 if messages else 0,
            "history_turns": len(history) if history else 0,
            "query_plan": query_plan or None,
        })

    # 5. Stream from DeepSeek
    step_llm = trace.add_step("LLM调用") if trace else None
    client = _get_async_llm()
    model = os.getenv("LLM_MODEL", "deepseek-v4-flash")

    try:
        if assistant_mode == "sql":
            from src.qa.sql_validator import (
                format_validation_feedback,
                validate_sql_answer,
            )

            yield {"type": "status", "content": "正在生成并校验 SQL…"}
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                stream=False,
                temperature=0.1,
                max_tokens=4096,
            )
            full_answer = response.choices[0].message.content or ""
            validation = validate_sql_answer(
                full_answer,
                dialect=sql_dialect,
                query_plan=query_plan,
            )
            attempts = 1

            if not validation.valid:
                yield {
                    "type": "status",
                    "content": "检测到字段、JOIN 或方言问题，正在自动修复…",
                }
                repair_messages = messages + [
                    {"role": "assistant", "content": full_answer},
                    {
                        "role": "user",
                        "content": (
                            "上一个回答没有通过物理 SQL 校验。请根据以下错误"
                            "重新输出完整回答；只能使用前文物理架构和已验证 JOIN，"
                            "不得解释或保留错误 SQL：\n"
                            + format_validation_feedback(validation)
                        ),
                    },
                ]
                repaired = await client.chat.completions.create(
                    model=model,
                    messages=repair_messages,
                    stream=False,
                    temperature=0.0,
                    max_tokens=4096,
                )
                full_answer = repaired.choices[0].message.content or ""
                validation = validate_sql_answer(
                    full_answer,
                    dialect=sql_dialect,
                    query_plan=query_plan,
                )
                attempts = 2

            if validation.valid:
                from src.qa.sql_query_planner import format_query_plan_markdown
                plan_markdown = format_query_plan_markdown(query_plan)
                if plan_markdown:
                    full_answer = f"{plan_markdown}\n\n{full_answer}"
                yield full_answer
            else:
                from src.qa.sql_query_planner import format_query_plan_markdown
                plan_markdown = format_query_plan_markdown(query_plan)
                full_answer = (
                    (f"{plan_markdown}\n\n" if plan_markdown else "")
                    + "### SQL 校验未通过\n"
                    "候选 SQL 包含无法由当前物理 Schema 验证的内容，"
                    "因此本次不展示 SQL。请补充或重新选择业务对象。\n\n"
                    + format_validation_feedback(validation)
                )
                yield full_answer

            if step_llm:
                step_llm.done(output={
                    "model": model,
                    "answer_length": len(full_answer),
                    "answer_tokens_estimate": len(full_answer) // 2,
                    "validation_attempts": attempts,
                    "sql_valid": validation.valid,
                    "validation_errors": validation.errors,
                })
        else:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                temperature=0.3,
                max_tokens=4096,
            )

            full_answer = ""
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    full_answer += token
                    yield token

            if step_llm:
                step_llm.done(output={
                    "model": model,
                    "answer_length": len(full_answer),
                    "answer_tokens_estimate": len(full_answer) // 2,
                })
    except Exception as e:
        if step_llm:
            step_llm.fail(str(e))
        yield f"\n\n❌ LLM 调用失败: {e}"


def extract_class_links(answer: str) -> list[str]:
    """Extract [[ClassName]] markers from the answer text."""
    return re.findall(r'\[\[(\w+)\]\]', answer)
