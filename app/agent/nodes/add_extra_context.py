import asyncio
from datetime import datetime

from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState, DateInfoState, DBInfoState
from app.core.log import logger
from app.repositories.mysql.dw import dw_mysql_repository


async def add_extra_context(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    await asyncio.sleep(1)
    # 获取流对象
    writer = runtime.stream_writer
    writer({"state": "添加额外上下文"})
    dw_mysql_repository = runtime.context["dw_mysql_repository"]

    try:
        # 1. 添加时间上下文信息
        today = datetime.today()
        date = today.strftime("%Y-%m-%d")

        weekday = today.strftime("%A")

        month = today.month
        quarter = f"Q{(month - 1) // 3 + 1}"

        # 封装数据
        date_info = DateInfoState(
            date=date,
            weekday=weekday,
            quarter=quarter,
        )
        # 2. 数据库相关信息
        # 2.1数据库方言
        # 2.2数据库版本

        db_info: DBInfoState = await dw_mysql_repository.get_db_info()

        logger.info(f"date_info:{date_info}")
        logger.info(f"添加额外上下文信息db_info:{db_info}")

        return {"date_info": date_info, "db_info": db_info}
    except Exception as e:
        logger.error(f"添加额外上下文异常:{str(e)}")
        raise
