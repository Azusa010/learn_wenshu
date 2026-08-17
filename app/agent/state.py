from typing import TypedDict

from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant
from app.models.value_info_es.value_info_es import ValueInfoEs


class DataAgentState(TypedDict):
    query: str
    error: bool|None = None
    keywords: list[str]
    recall_columns:list[ColumnInfoQdrant]
    recall_metrics:list[MetricInfoQdrant]
    recall_values:list[ValueInfoEs]