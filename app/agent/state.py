from typing import TypedDict

from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant
from app.models.value_info_es.value_info_es import ValueInfoEs


class ColumnInfoState(TypedDict):
    name: str
    type: str
    role: str
    examples: list
    description: str
    alias: list[str]


class TableInfoState(TypedDict):
    name: str
    role: str
    description: str
    columns: list[ColumnInfoState]

class MetricInfoState(TypedDict):
    name: str
    description: str
    relevant_columns: list[str]
    alias: list[str]

class DateInfoState(TypedDict):
    date: str
    weekday : str
    quarter : str

class DBInfoState(TypedDict):
    version: str
    dialect: str


class DataAgentState(TypedDict):
    query: str
    error: bool | None = None
    keywords: list[str]
    recall_columns: list[ColumnInfoQdrant]
    recall_metrics: list[MetricInfoQdrant]
    recall_values: list[ValueInfoEs]
    table_infos:list[TableInfoState]
    metric_infos: list[MetricInfoState]
    date_info: DateInfoState
    db_info: DBInfoState
    sql:str