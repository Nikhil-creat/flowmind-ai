from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.cache import is_redis_connected
from app.core.config import get_settings

settings = get_settings()

# Uses Redis as the shared counter store when available (correct across
# multiple server processes/instances); falls back to in-memory per-process
# limits otherwise, so rate limiting still works in a single-process dev run.
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL if is_redis_connected() else "memory://",
)
