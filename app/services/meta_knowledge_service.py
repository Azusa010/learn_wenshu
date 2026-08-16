from pathlib import Path

from omegaconf import OmegaConf

from app.conf.meta_config import MetaConfig
from app.core.log import logger


async def build(self, config_path: Path):
    pass
    # 1.加载配置文件
    context = OmegaConf.load(config_path)
    schema = OmegaConf.structured(MetaConfig)
    meta_config: MetaConfig = OmegaConf.to_object(OmegaConf.merge(schema, context))
    logger.info("加载配置文件完成")
    if meta_config.tables:
    # 2.处理表信息
        pass
    # 2.1 保存表信息到meta数据库
    # 2.2 为字段信息建立向量索引
    # 2.3 为字段取值建立全文索引

    # 3.处理指标信息
    # 3.1 保存指标信息到meta数据库
    # 3.2 为指标信息建立向量索引
