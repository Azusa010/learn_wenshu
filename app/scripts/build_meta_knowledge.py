import asyncio
from argparse import ArgumentParser
from pathlib import Path

from app.clients.embedding_client_manager import embedding_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.clients.sql_client_manager import meta_mysql_client_manager, dw_mysql_client_manager
from app.core.log import logger
from app.repositories.es.value_es_repository import ValueEsRepository
from app.repositories.mysql.dw.dw_mysql_repository import DwMysqlRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository
from app.services.meta_knowledge_service import MetaKnowledgeService


async def _check_external_services():
    """在写入 meta 数据库前确认依赖服务可用。"""
    try:
        await qdrant_client_manager.client.get_collections()
    except Exception as exc:
        raise RuntimeError("Qdrant 服务连接失败，请检查 localhost:6333") from exc

    if not await es_client_manager.client.ping():
        raise RuntimeError("Elasticsearch 服务连接失败，请检查 localhost:9200")

    try:
        await embedding_manager.client.aembed_query("health check")
    except Exception as exc:
        raise RuntimeError("Embedding 服务连接失败，请检查 localhost:8081") from exc


async def build(config_path: Path):
    initialized_managers = []
    try:
        # 初始化 engine 和客户端
        for manager in (
            meta_mysql_client_manager,
            dw_mysql_client_manager,
            qdrant_client_manager,
            es_client_manager,
        ):
            manager.init()
            initialized_managers.append(manager)
        embedding_manager.init()

        await _check_external_services()
        logger.info("外部依赖服务检查完成")

        # 创建 session
        async with meta_mysql_client_manager.session_factory() as meta_session, dw_mysql_client_manager.session_factory() as dw_session:
            meta_mysql_repository = MetaMysqlRepository(meta_session)
            dw_mysql_repository = DwMysqlRepository(dw_session)
            column_qdrant_repository = ColumnQdrantRepository(qdrant_client_manager.client)
            value_es_repository = ValueEsRepository(es_client_manager.client)
            metric_qd_repository = MetricQdrantRepository(qdrant_client_manager.client)
            meta_knowledge_service = MetaKnowledgeService(
                meta_mysql_repository=meta_mysql_repository,
                dw_mysql_repository=dw_mysql_repository,
                column_qdrant_repository=column_qdrant_repository,
                embedding_client=embedding_manager.client,
                value_es_repository=value_es_repository,
                metric_qdrant_repository=metric_qd_repository,
            )
            await meta_knowledge_service.build(config_path)
    finally:
        # 即使构建失败，也要释放已经初始化的连接。
        for manager in reversed(initialized_managers):
            try:
                await manager.close()
            except Exception:
                logger.exception("关闭客户端资源失败: {}", type(manager).__name__)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "-c", "--conf"
    )
    args = parser.parse_args()
    config_path = Path(args.conf)
    try:
        asyncio.run(build(config_path))
        logger.info(f"build complete")
    except Exception as e:
        logger.exception(f"构建元知识库失败")
