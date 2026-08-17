import asyncio

from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def filter_metric(state:DataAgentState,runtime:Runtime[DataAgentContext]):
    await asyncio.sleep(1)
    # 获取流对象
    writer = runtime.stream_writer
    writer({"state": "过滤指标"})
    try:
        pass
    except Exception as e:
        logger.error(e)
        raise