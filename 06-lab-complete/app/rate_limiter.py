"""Atomic Redis sliding-window rate limiter shared by all workers/instances."""
import secrets
import hashlib
import time

from fastapi import HTTPException

from app.config import settings
from app.redis_client import r


_WINDOW_MS = 60_000
_CHECK_AND_ADD = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local member = ARGV[4]
redis.call('ZREMRANGEBYSCORE', key, '-inf', now - window)
local count = redis.call('ZCARD', key)
if count >= limit then
  local first = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
  local retry = window
  if first[2] then retry = math.max(1, tonumber(first[2]) + window - now) end
  return {0, retry}
end
redis.call('ZADD', key, now, member)
redis.call('PEXPIRE', key, window)
return {1, 0}
"""


def check_rate_limit(key: str) -> None:
    now_ms = time.time_ns() // 1_000_000
    accepted, retry_ms = r.eval(
        _CHECK_AND_ADD,
        1,
        "rate-limit:" + hashlib.sha256(key.encode("utf-8")).hexdigest(),
        now_ms,
        _WINDOW_MS,
        settings.rate_limit_per_minute,
        f"{now_ms}:{secrets.token_hex(8)}",
    )
    if not int(accepted):
        retry_seconds = max(1, (int(retry_ms) + 999) // 1000)
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_seconds)},
        )
