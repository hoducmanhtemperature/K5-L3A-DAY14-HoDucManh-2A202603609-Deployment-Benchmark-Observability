"""Shared Redis connection; creating the client does not connect to Redis."""
import redis

from app.config import settings


r = redis.Redis.from_url(
    settings.redis_url,
    decode_responses=True,
    socket_connect_timeout=1,
    socket_timeout=1,
    health_check_interval=30,
)


def redis_healthy() -> bool:
    try:
        return bool(r.ping())
    except (redis.RedisError, OSError, TimeoutError):
        return False


def close_redis() -> None:
    r.close()
