"""Track mock/LLM token costs in Redis, partitioned by UTC day."""
from datetime import datetime, timezone

from fastapi import HTTPException

from app.config import settings
from app.redis_client import r

# Approximate input/output prices in USD per 1K tokens.
PRICE_INPUT_PER_1K = 0.00015
PRICE_OUTPUT_PER_1K = 0.0006


def _daily_key() -> str:
    return "llm-cost-usd:" + datetime.now(timezone.utc).strftime("%Y-%m-%d")


def check_budget() -> None:
    """Gọi TRƯỚC khi gọi LLM. Hết budget → raise HTTPException(status_code=402)."""
    spent = float(r.get(_daily_key()) or 0)
    if spent >= settings.daily_budget_usd:
        raise HTTPException(status_code=402, detail="Daily LLM budget exceeded")


def record_cost(input_tokens: int, output_tokens: int) -> float:
    """Gọi SAU khi gọi LLM. Cộng chi phí của request vào tổng, trả về chi phí request."""
    cost = (max(0, input_tokens) / 1000 * PRICE_INPUT_PER_1K
            + max(0, output_tokens) / 1000 * PRICE_OUTPUT_PER_1K)
    key = _daily_key()
    r.incrbyfloat(key, cost)
    r.expire(key, 2 * 24 * 60 * 60)
    return cost
