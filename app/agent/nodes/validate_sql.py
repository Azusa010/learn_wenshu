import asyncio

from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def validate_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    await asyncio.sleep(1)
    # 获取流对象
    writer = runtime.stream_writer
    writer({"state": "校验sql"})
    sql = state["sql"]
    try:
        dw_mysql_repository = runtime.context["dw_mysql_repository"]
        dw_mysql_repository.validate_sql(sql)
        logger.info(f"sql验证正确:{sql}")
        return {"error": None}
    except Exception as e:
        logger.error(f"sql验证失败:{sql}")
        return {"error": f"sql验证异常{str(e)}"}
