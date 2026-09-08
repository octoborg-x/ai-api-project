import hmac
import os

from fastapi import HTTPException, Request


def authenticate(request: Request) -> str:
    """Validate a Bearer token and return the authenticated principal."""
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    expected = os.getenv("API_AUTH_TOKEN")

    if scheme.lower() != "bearer" or not token or not expected:
        raise HTTPException(status_code=401, detail="Missing or invalid bearer token")

    if not hmac.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="Missing or invalid bearer token")

    return "api-token"
