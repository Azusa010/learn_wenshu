import asyncio

from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.models.mysql.column_info_mysql import ColumnInfoMySQL
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant
from app.models.value_info_es.value_info_es import ValueInfoEs
from app.repositories.mysql.meta import meta_mysql_repository


def convert_column_info_from_mysql_to_qdrant(column_info_mysql: ColumnInfoMySQL) -> ColumnInfoQdrant:
    return ColumnInfoQdrant(
        id=column_info_mysql.id,
        name=column_info_mysql.name,
        description=column_info_mysql.description,
        role=column_info_mysql.role,
        type=column_info_mysql.type,
        examples=column_info_mysql.examples,
        table_id=column_info_mysql.table_id,
        alias=column_info_mysql.alias,
    )


async def merge_retrieved_info(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    await asyncio.sleep(1)
    # 获取流对象
    writer = runtime.stream_writer
    writer({"state": "合并召回信息"})

    # 获取召回的字段信息
    recall_columns: list[ColumnInfoQdrant] = state["recall_columns"]
    # 获取召回的指标信息
    recall_metrics: list[MetricInfoQdrant] = state["recall_metrics"]
    # 获取召回的取值信息
    recall_values: list[ValueInfoEs] = state["recall_values"]

    # 获取repository
    meta_mysql_repository = runtime.context["meta_mysql_repository"]

    retrieved_column_maps: dict[str, ColumnInfoQdrant] = {recall_column["id"]: recall_column for recall_column in
                                                          recall_columns}
    for recall_metric in recall_metrics:
        for e in recall_metric["relevant_columns"]:
            if e not in retrieved_column_maps:
                column_info_mysql: ColumnInfoMySQL = await meta_mysql_repository.get_column_info_by_id(e)
                retrieved_column_maps[e] = convert_column_info_from_mysql_to_qdrant(column_info_mysql)
