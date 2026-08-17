import asyncio
import keyword

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant
from app.prompt.prompt_loader import load_prompt
from app.repositories.qdrant import column_qdrant_repository


async def recall_column(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    await asyncio.sleep(1)
    # 获取流对象
    writer = runtime.stream_writer
    writer({"state": "召回字段"})
    try:
        embedding_client = runtime.context["embedding_client"]
        column_qdrant_repository = runtime.context["column_qdrant_repository"]

        query = state["query"]
        keywords = state["keywords"]
        prompt = PromptTemplate(template=load_prompt("extend_keywords_for_column_recall"), input_variables=["query"])
        output_parser = JsonOutputParser()
        chain = prompt | llm | output_parser
        result = await chain.ainvoke({"query": query})
        keywords = set(keywords + result)

        recall_columns_map: dict[str, ColumnInfoQdrant] = {}

        for keyword in keywords:
            embeddings = embedding_client.aembed_query(keyword)
            payloads: list[ColumnInfoQdrant] = column_qdrant_repository.search(embeddings)
            for payload in payloads:
                column_id = payload["id"]
                if column_id not in recall_columns_map:
                    recall_columns_map[column_id] = payload

        recall_columns = list[ColumnInfoQdrant] = list(recall_columns_map.values())
        logger.info(f"召回字段信息:{list(recall_columns_map.keys())}")
        return {"recall_columns": recall_columns}
    except Exception as e:
        logger.error(f"召回字段信息异常{str(e)}")
        raise
