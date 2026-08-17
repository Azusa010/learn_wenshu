import asyncio

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant
from app.prompt.prompt_loader import load_prompt


async def recall_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    await asyncio.sleep(1)
    # 获取流对象
    writer = runtime.stream_writer
    writer({"state": "召回指标"})
    try:
        embedding_client = runtime.context["embedding_client"]
        qdrant_client = runtime.context["metric_qdrant_repository"]

        query = state["query"]
        keywords = state["keywords"]
        prompt = PromptTemplate(template=load_prompt("extend_keywords_for_metric_recall"), input_variables=["query"])
        output_parser = JsonOutputParser()
        chain = prompt | llm | output_parser
        result = await chain.ainvoke({"query": query})
        keywords = set(keywords + result)

        logger.info(f"扩展后关键字:{keywords}")

        retrieved_metric_map: dict[str, MetricInfoQdrant] = {}
        for keyword in keywords:
            embeddings = await embedding_client.aembed_query(keyword)

            payloads: list[MetricInfoQdrant] = await qdrant_client.search_embedding(embeddings)

            for payload in payloads:
                metric_id = payload["id"]
                if metric_id not in retrieved_metric_map:
                    retrieved_metric_map[metric_id] = payload

        recall_metrics: list[MetricInfoQdrant] = list(retrieved_metric_map.values())
        logger.info(f"召回指标成功:{retrieved_metric_map.keys()}")
        return {"recall_metrics": recall_metrics}

    except Exception as e:
        logger.error(f"召回指标异常:{str(e)}")
        raise
