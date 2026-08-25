"""
Security middleware, CORS, security headers, dan environment validation.
"""
from __future__ import annotations

import os
from typing import Dict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response


def validate_env() -> Dict[str, str]:
    """Validasi environment variables wajib. Mengembalikan dict errors."""
    errors = {}
    required_vars = [
        "FASTRA_DT_SECRET_KEY",
        "FASTRA_DT_API_KEY",
        "FASTRA_DT_ADMIN_PASSWORD",
        "FASTRA_DT_QS_PASSWORD",
        "FASTRA_DT_VIEWER_PASSWORD",
    ]
    for var in required_vars:
        if not os.getenv(var):
            errors[var] = "missing"
    return errors
