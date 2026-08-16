from argparse import ArgumentParser
from pathlib import Path

from app.clients.embedding_client_manager import embedding_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.clients.sql_client_manager import meta_mysql_client_manager, dw_mysql_client_manager
from app.core.log import logger


async def build(config_path: Path):
    """
    构建元知识库函数
    用于执行构建元知识库相关的业务逻辑，例如加载配置、初始化数据等
    :return:
    """
    meta_mysql_client_manager.init()
    dw_mysql_client_manager.init()
    qdrant_client_manager.init()
    embedding_manager.init()
    es_client_manager.init()

    async with meta_mysql_client_manager.session_factory() as meta_session,dw_mysql_client_manager.session_factory() as dw_session:
        pass

    logger.info("Building meta knowledge...")

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "-c","--conf"
    )
    args = parser.parse_args()
    config_path = Path(args.conf)
    build()
