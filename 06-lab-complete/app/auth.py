"""API key authentication for protected agent endpoints."""
import secrets
from typing import Optional

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from app.config import settings


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """Return the supplied key, or reject missing, unset, and incorrect keys."""
    expected = settings.agent_api_key
    if not expected or not api_key or not secrets.compare_digest(api_key, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key",
                            headers={"WWW-Authenticate": "ApiKey"})
    return api_key
