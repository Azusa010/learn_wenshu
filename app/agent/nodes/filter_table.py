import asyncio

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState, TableInfoState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt


async def filter_table(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    await asyncio.sleep(1)
    # 获取流对象
    writer = runtime.stream_writer
    writer({"stage": "过滤表信息"})
    try:
        query = state["query"]
        table_infos: list[TableInfoState] = state["table_infos"]

        # 1. 调用模型,返回与业务相关的表信息
        # 1.1 定义提示词模板
        prompt = PromptTemplate(template=load_prompt("filter_table_info"), input_variables=["query", "table_infos"])
        output_parser = JsonOutputParser()
        chain = prompt | llm | output_parser
        result = await chain.ainvoke({"query": query, "table_infos": table_infos})

        # 2. 循环遍历表信息，根据业务相关结果，剔除表信息
        for table_info in table_infos:
            table_name = table_info["name"]

            if table_name not in result[:]:
                table_infos.remove(table_info)
            else:
                # 模型处理后的结构
                result_column = result[table_name]
                for columns_info in table_info["columns"][:]:
                    column_name = columns_info["name"]
                    if column_name not in result_column:
                        table_info["columns"].remove(columns_info)
        logger.info(f"过滤表成功{table_infos}")
        return {"table_infos": table_infos}
    except Exception as e:
        logger.error(f"过滤表异常f{str(e)}")
        raise
