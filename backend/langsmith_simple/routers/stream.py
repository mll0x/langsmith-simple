import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ..redis_client import get_redis

router = APIRouter(tags=["stream"])


@router.get("/runs/stream")
async def stream_runs(project_name: str | None = None):
    channel = f"runs:{project_name or 'default'}"
    r = get_redis()
    pubsub = r.pubsub()
    await pubsub.subscribe(channel)

    async def event_generator():
        yield f"data: {json.dumps({'type': 'connected', 'channel': channel})}\n\n"
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=15.0)
                if message and message.get("type") == "message":
                    data = message.get("data", "{}")
                    yield f"data: {data}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")
