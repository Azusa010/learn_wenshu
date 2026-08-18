import uuid

import uvicorn
from fastapi import FastAPI,Request

from app.api.routers.query_router import query_router
from app.core.context import request_id_ctx_var
from app.core.lifespan import lifespan

app = FastAPI(lifespan=lifespan)

app.include_router(query_router)

# 整合中间件
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    request_id_ctx_var.set(uuid.uuid4())
    response = await call_next(request)
    return response