from typing import TypedDict


class DataAgentState(TypedDict):
    query: str
    error: bool|None = None