import asyncio

from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.models.mysql.column_info_mysql import ColumnInfoMySQL
from app.models.mysql.table_info_mysql import TableInfoMySQL
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

    # 根据召回指标取值
    retrieved_column_maps: dict[str, ColumnInfoQdrant] = {recall_column["id"]: recall_column for recall_column in
                                                          recall_columns}
    for recall_metric in recall_metrics:
        for e in recall_metric["relevant_columns"]:
            if e not in retrieved_column_maps:
                column_info_mysql: ColumnInfoMySQL = await meta_mysql_repository.get_column_info_by_id(e)
                retrieved_column_maps[e] = convert_column_info_from_mysql_to_qdrant(column_info_mysql)

    # 根据召回字段取值
    for recall_value in recall_values:
        column_id = recall_value["column_id"]
        column_value = recall_value["value"]
        if column_id not in retrieved_column_maps:
            column_info_mysql = await meta_mysql_repository.get_column_info_by_id(column_id)
            retrieved_column_maps[column_id] = convert_column_info_from_mysql_to_qdrant(column_info_mysql)

        if column_value not in retrieved_column_maps[column_id]["examples"]:
            retrieved_column_maps[column_id]["examples"].append(column_value)

    # 3.划分字段以表为单位
    retrieved_table_maps: dict[str, list[ColumnInfoQdrant]] = {}
    for column_info in retrieved_column_maps.values():
        table_id = column_info["table_id"]
        if table_id not in retrieved_table_maps:
            retrieved_table_maps[table_id] = []

    # 4.遍历表字段结构数据，增加主外键数据
    for table_id, column_list in retrieved_table_maps.items():
        column_infos: list[ColumnInfoMySQL] = await meta_mysql_repository.get_key_column_by_table_id(table_id)
        # 判断
        column_ids: list[str] = [columns["id"] for columns in column_list]
        for column_info in column_infos:
            column_id = column_info.id
            if column_id not in column_ids:
                column_list.append(convert_column_info_from_mysql_to_qdrant(column_info))
