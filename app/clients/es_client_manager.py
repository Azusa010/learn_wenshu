import asyncio
from typing import Optional

from elasticsearch import AsyncElasticsearch

from conf.app_config import ESConfig, app_config


class EsClientManager:
    def __init__(self, config: ESConfig):
        self.client: Optional[AsyncElasticsearch] = None
        self.config = config

    def _get_url(self):
        return f"http://{self.config.host}:{self.config.port}"

    def init(self):
        self.client = AsyncElasticsearch(
            hosts=[self._get_url()],
        )

    async def close(self):
        await self.client.close()


es_client_manager = EsClientManager(app_config.es)

if __name__ == "__main__":
    es_client_manager.init()
    INDEX_NAME = "my-books"


    async def test():
        client = es_client_manager.client

        try:
            if not await client.indices.exists(index=INDEX_NAME):
                await client.indices.create(
                    index=INDEX_NAME,
                    mappings={
                        "dynamic": False,
                        "properties": {
                            "name": {"type": "text"},
                            "author": {"type": "text"},
                            "release_date": {
                                "type": "date",
                                "format": "yyyy-MM-dd",
                            },
                            "page_count": {"type": "integer"},
                        },
                    },
                )

                await client.bulk(
                    operations=[
                        # 原来的数据
                    ],
                )

            # 搜索放在 if 外面，否则索引已存在时不会搜索
            resp = await client.search(
                index=INDEX_NAME,
                query={
                    "match": {
                        "name": "brave",
                    }
                },
            )
            print(resp)

        finally:
            await es_client_manager.close()


    asyncio.run(test())
