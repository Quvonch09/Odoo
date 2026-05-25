from __future__ import annotations

import json
from typing import Any

from redis.asyncio import Redis

from app.core.config import get_settings

settings = get_settings()
redis_client = Redis.from_url(settings.redis_url, decode_responses=True)


async def ping_redis() -> bool:
    return bool(await redis_client.ping())


async def get_cache(key: str) -> Any | None:
    value = await redis_client.get(key)
    return None if value is None else json.loads(value)


async def set_cache(key: str, value: Any, ttl: int | None = None) -> None:
    await redis_client.set(key, json.dumps(value, default=str), ex=ttl or settings.redis_default_ttl)
