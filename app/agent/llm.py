from langchain.chat_models import init_chat_model

from conf.app_config import app_config

model = init_chat_model(
    model=app_config.llm.model_name,
    model_provider="openai",
    base_url=app_config.llm.base_url,
    api_key=app_config.llm.api_key,
    temperature=0
)

if __name__ == "__main__":
    for chunk in model.stream("简单介绍一下你的模型"):
        print(chunk.text, end="", flush=True)
