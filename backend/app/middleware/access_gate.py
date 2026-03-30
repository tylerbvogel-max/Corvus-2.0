"""Simple access gate middleware — shared access key authentication.

If CORVUS_ACCESS_KEY is set in the environment, all API requests must include
it as a Bearer token in the Authorization header. Static file requests (frontend)
and the /tenant endpoint are exempt so the login page can load.

If CORVUS_ACCESS_KEY is not set, the gate is disabled (open access).
"""

import os

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Exempt paths that must be accessible without auth (frontend assets, login check)
_EXEMPT_PREFIXES = ("/tenant", "/favicon", "/assets/", "/corvus-logo", "/index.html")


class AccessGateMiddleware(BaseHTTPMiddleware):
    """Check Bearer token against CORVUS_ACCESS_KEY on every request."""

    def __init__(self, app, access_key: str | None = None):
        super().__init__(app)
        self._key = access_key or os.environ.get("CORVUS_ACCESS_KEY", "")

    async def dispatch(self, request: Request, call_next):
        # If no key configured, gate is disabled
        if not self._key:
            return await call_next(request)

        path = request.url.path

        # Let frontend static files and tenant config through
        if path == "/" or any(path.startswith(p) for p in _EXEMPT_PREFIXES):
            return await call_next(request)

        # Check Authorization header
        auth = request.headers.get("Authorization", "")
        if auth == f"Bearer {self._key}":
            return await call_next(request)

        return JSONResponse(
            status_code= 401,
            content={"detail": "Access key required"},
        )
