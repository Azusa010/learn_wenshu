import asyncio
from typing import Annotated

from fastapi import APIRouter
from fastapi.params import Depends
from starlette.responses import StreamingResponse

from app.api.dependencies import get_query_service
from app.api.schemas.query_schema import QuerySchema
from app.services.query_service import QueryService

query_router = APIRouter()


@query_router.get("/api/query")
async def query(query: QuerySchema, service: Annotated[QueryService, Depends(get_query_service)]):
    return StreamingResponse(service.query(query),media_type='text/event-stream')