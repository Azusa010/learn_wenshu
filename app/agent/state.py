from typing import TypedDict

from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant


class DataAgentState(TypedDict):
    query: str
    error: bool|None = None
    keywords: list[str]
    recall_columns:list[ColumnInfoQdrant]