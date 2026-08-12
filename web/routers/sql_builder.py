from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.qa.sql_query_builder import (
    MAX_QUERY_OBJECTS,
    build_query_builder_plan,
)


router = APIRouter()


class SqlBuilderPlanRequest(BaseModel):
    selected_nodes: list[str] = Field(
        default_factory=list,
        max_length=MAX_QUERY_OBJECTS,
    )
    dialect: Literal["oracle", "sqlserver"] = "oracle"
    join_overrides: list["SqlBuilderJoinOverride"] = Field(
        default_factory=list,
        max_length=MAX_QUERY_OBJECTS * 2,
    )


class SqlBuilderJoinOverride(BaseModel):
    from_table: str = Field(min_length=1)
    from_field: str = Field(min_length=1)
    to_table: str = Field(min_length=1)
    to_field: str = Field(min_length=1)


@router.post("/api/sql-builder/plan")
async def sql_builder_plan(req: SqlBuilderPlanRequest):
    try:
        return build_query_builder_plan(
            req.selected_nodes,
            dialect=req.dialect,
            join_overrides=[item.model_dump() for item in req.join_overrides],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
