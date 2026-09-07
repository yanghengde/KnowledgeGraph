"""Batch translation used by ontology import description enrichment."""

import json
from typing import Any

from openai import OpenAI


def compact(value: Any) -> str:
    return " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split())


def translate_batch(client: OpenAI, model: str, direction: str, values: list[str]) -> list[str]:
    rows = {str(index): value for index, value in enumerate(values)}
    if direction == "en_to_zh":
        instruction = (
            "你是 Siemens Opcenter Execution（Camstar）MES 术语专家。"
            "将每条英文对象或字段说明忠实翻译成简洁准确的简体中文。"
            "不得修改技术标识符、产品名、缩写、枚举值和引用类型，不得补造功能。"
            "仅返回 JSON 对象，键必须与输入完全一致，值为中文说明。"
        )
    else:
        instruction = (
            "You are a Siemens Opcenter Execution (Camstar) MES terminology expert. "
            "Translate each Chinese object or field description into concise, accurate English. "
            "Preserve identifiers, product names, abbreviations, enum values, and referenced types. "
            "Do not invent behavior. Return only a JSON object with exactly the input keys."
        )
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": instruction},
            {"role": "user", "content": json.dumps(rows, ensure_ascii=False)},
        ],
    )
    parsed = json.loads(response.choices[0].message.content or "{}")
    if set(parsed) != set(rows):
        raise ValueError("Translation response keys do not match the input batch")
    result = [compact(parsed[str(index)]) for index in range(len(values))]
    if any(not value for value in result):
        raise ValueError("Translation response contains an empty description")
    return result
