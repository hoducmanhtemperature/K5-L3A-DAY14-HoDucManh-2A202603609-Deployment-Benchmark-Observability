"""Twelve-factor configuration loaded from the process environment."""
from dataclasses import dataclass
import os


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


def _float_env(name: str, default: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc
    if value < 0:
        raise ValueError(f"{name} must not be negative")
    return value


@dataclass(frozen=True)
class Settings:
    port: int
    environment: str
    agent_api_key: str
    redis_url: str
    rate_limit_per_minute: int
    daily_budget_usd: float

    @classmethod
    def from_env(cls) -> "Settings":
        rate_limit = _int_env("RATE_LIMIT_PER_MINUTE", 10)
        if rate_limit < 1:
            raise ValueError("RATE_LIMIT_PER_MINUTE must be at least 1")
        return cls(
            port=_int_env("PORT", 8000),
            environment=os.getenv("ENVIRONMENT", "development"),
            agent_api_key=os.getenv("AGENT_API_KEY", ""),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            rate_limit_per_minute=rate_limit,
            daily_budget_usd=_float_env("DAILY_BUDGET_USD", 1.0),
        )


settings = Settings.from_env()
