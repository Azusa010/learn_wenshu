from typing import TypedDict

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository


class DataAgentContext(TypedDict):
    embedding_client:HuggingFaceEndpointEmbeddings
    column_qdrant_repository:ColumnQdrantRepository
