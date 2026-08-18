import asyncio

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.models.value_info_es.value_info_es import ValueInfoEs
from app.prompt.prompt_loader import load_prompt
from app.repositories.es import value_es_repository


async def recall_value(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 获取流对象
    writer = runtime.stream_writer
    writer({"stage": "召回字段值"})
    try:
        value_es_repository = runtime.context["value_es_repository"]
        query = state["query"]
        keywords = state["keywords"]
        prompt = PromptTemplate(template=load_prompt("extend_keywords_for_value_recall"), input_variables=["query"])
        output_parser = JsonOutputParser()
        chain = prompt | llm | output_parser
        result = await chain.ainvoke({"query": query})
        keywords = set(keywords + result)

        value_maps: dict[str, ValueInfoEs] = {}
        for keyword in keywords:
            values: list[ValueInfoEs] = await value_es_repository.search(keyword)
            for value in values:
                value_id = value["id"]
                if value_id not in value_maps:
                    value_maps[value_id] = value

        recall_values:list[ValueInfoEs] =list(value_maps.values())

        logger.info(f"召回字段取值:{list(value_maps.keys())}")
        return {"recall_values": recall_values}

    except Exception as e:
        logger.error(f"召回字段取值异常{str(e)}")
        raise
