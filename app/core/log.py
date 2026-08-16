import asyncio
import uuid

import sys
from pathlib import Path

from loguru import logger

from app.core.context import request_id_ctx_var
from conf.app_config import app_config

log_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "  # 绿色显示日志时间（精确到毫秒）
    "<level>{level: <8}</level> | "                      # 按级别颜色显示日志级别（左对齐，占8个字符）
    "<magenta>request_id - {extra[request_id]}</magenta> | "  # 品红色显示request_id（从日志extra中获取）
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "  # 青色显示日志所在文件、函数、行号
    "<level>{message}</level>"  # 按级别颜色显示日志正文
)

def inject_request_id(record):
    try:
        request_id = request_id_ctx_var.get()
    except Exception as e:
        request_id = uuid.uuid4()

    record["extra"]["request_id"] = request_id

logger.remove()

logger = logger.patch(inject_request_id)

if app_config.logging.console.enable:
    logger.add(sink=sys.stdout,format=log_format,level=app_config.logging.console.level)

if app_config.logging.file.enable:
    path = Path(app_config.logging.file.path)
    path.mkdir(parents=True, exist_ok=True)
    logger.add(
        sink=path/"app.log",
        format=log_format,
        level=app_config.logging.file.level,
        rotation=app_config.logging.file.rotation,
        retention=app_config.logging.file.retention,
        encoding="utf-8",
    )

if __name__ == "__main__":
    async  def graph(request:str):
        id = request_id_ctx_var.get()
        logger.info(f"request_id - {id}")

    async def test1():
        request_id_ctx_var.set("111111111111")
        await asyncio.sleep(1)
        await graph("request-1")

    async def test2():
        request_id_ctx_var.set("222222222222")
        await asyncio.sleep(1)
        await graph("request-2")

    async def main():
        await asyncio.gather(test1(), test2())

    asyncio.run(main())