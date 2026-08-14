import asyncio
from typing import Optional

from elasticsearch import AsyncElasticsearch

from conf.app_config import ESConfig, app_config


class EsClientManager:
    def __init__(self, config: ESConfig):
        self.client: Optional[AsyncElasticsearch] = None
        self.config = config

    def get_url(self):
        return f"http://{self.config.host}:{self.config.port}"

    def init(self):
        self.client = AsyncElasticsearch(
            hosts=[self.get_url()],
        )

    async def close(self):
        await self.client.close()


es_client_manager = EsClientManager(app_config.es)

if __name__ == "__main__":
    es_client_manager.init()


    async def test():
        client = es_client_manager.client

        if not await client.indices.exists(index="my_book"):
            await client.indices.create(
                index="my-books",
                mappings={
                    "dynamic": False,
                    "properties": {
                        "name": {
                            "type": "text"
                        },
                        "author": {
                            "type": "text"
                        },
                        "release_date": {
                            "type": "date",
                            "format": "yyyy-MM-dd"
                        },
                        "page_count": {
                            "type": "integer"
                        }
                    }
                },
            )

            # 插入数据
            # 参考：https://www.elastic.co/guide/en/elasticsearch/reference/8.19/getting-started.html#getting-started-add-multiple-documents
            await client.bulk(
                operations=[
                    {
                        "index": {
                            "_index": "my-books"
                        }
                    },
                    {
                        "name": "Revelation Space",
                        "author": "Alastair Reynolds",
                        "release_date": "2000-03-15",
                        "page_count": 585
                    },
                    {
                        "index": {
                            "_index": "my-books"
                        }
                    },
                    {
                        "name": "1984",
                        "author": "George Orwell",
                        "release_date": "1985-06-01",
                        "page_count": 328
                    },
                    {
                        "index": {
                            "_index": "my-books"
                        }
                    },
                    {
                        "name": "Fahrenheit 451",
                        "author": "Ray Bradbury",
                        "release_date": "1953-10-15",
                        "page_count": 227
                    },
                    {
                        "index": {
                            "_index": "my-books"
                        }
                    },
                    {
                        "name": "Brave New World",
                        "author": "Aldous Huxley",
                        "release_date": "1932-06-01",
                        "page_count": 268
                    },
                    {
                        "index": {
                            "_index": "my-books"
                        }
                    },
                    {
                        "name": "The Handmaids Tale",
                        "author": "Margaret Atwood",
                        "release_date": "1985-06-01",
                        "page_count": 311
                    }
                ],
            )

            # 搜索
            # 参考：https://www.elastic.co/guide/en/elasticsearch/reference/8.19/getting-started.html#getting-started-match-query
            resp = await client.search(
                index="my-books",
                query={
                    "match": {
                        "name": "brave"
                    }
                },
            )
            print(resp)


        await es_client_manager.close()


    asyncio.run(test())