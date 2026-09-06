"""
A tiny cache abstraction so the app is faster and more resilient under load,
but never *requires* Redis to run - if REDIS_URL isn't set (or Redis is
unreachable), we transparently fall back to an in-process TTL cache.
"""
from __future__ import annotations

import json
import time
from typing import Any

from app.core.config import get_settings

settings = get_settings()

_memory_store: dict[str, tuple[float, str]] = {}
_redis_client = None

if settings.REDIS_URL:
    try:
        import redis

        _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True, socket_timeout=1)
        _redis_client.ping()
    except Exception:  # noqa: BLE001
        _redis_client = None  # Redis configured but unreachable - degrade gracefully


def get(key: str) -> Any | None:
    if _redis_client:
        try:
            raw = _redis_client.get(key)
            return json.loads(raw) if raw else None
        except Exception:  # noqa: BLE001
            return None

    entry = _memory_store.get(key)
    if not entry:
        return None
    expires_at, raw = entry
    if time.time() > expires_at:
        _memory_store.pop(key, None)
        return None
    return json.loads(raw)


def set(key: str, value: Any, ttl: int | None = None) -> None:
    ttl = ttl or settings.CACHE_TTL_SECONDS
    raw = json.dumps(value)
    if _redis_client:
        try:
            _redis_client.setex(key, ttl, raw)
            return
        except Exception:  # noqa: BLE001
            pass
    _memory_store[key] = (time.time() + ttl, raw)


def is_redis_connected() -> bool:
    return _redis_client is not None
