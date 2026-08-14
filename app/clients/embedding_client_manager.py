import asyncio
from typing import Optional

import httpx
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_openai import OpenAIEmbeddings

from conf.app_config import EmbeddingConfig, app_config


class EmbeddingClientManager:
    def __init__(self,config:EmbeddingConfig):
        self.client:Optional[OpenAIEmbeddings] = None
        self.config = config

    def _get_url(self):
        return f"http://{self.config.host}:{self.config.port}"

    def init(self):
        self.client = OpenAIEmbeddings(
            model=self.config.model,
            base_url=f"{self._get_url()}/v1",
            api_key="not-needed",
            check_embedding_ctx_length=False,
            http_client=httpx.Client(trust_env=False),
            http_async_client=httpx.AsyncClient(trust_env=False),
        )

embedding_manager = EmbeddingClientManager(app_config.embedding)

if __name__ == "__main__":
    embedding_manager.init()
    query = embedding_manager.client.embed_query("hello world")
    print(len(query))
    print(query)