import json

import redis.asyncio as redis

from .config import settings

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(settings.redis_url, decode_responses=True)
    return _client


async def publish_run_event(project_name: str, event: dict) -> None:
    r = get_redis()
    await r.publish(f"runs:{project_name}", json.dumps(event))
