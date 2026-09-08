# fastra_core\digital_twin\security.py

from __future__ import annotations

import logging
import os
import re
from typing import Any, List

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("fastra_core.digital_twin.security")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any) -> Response:
        if not isinstance(request, Request):
            logger.error("SECURITY_MIDDLEWARE_INVALID_REQUEST_INSTANCE")
            raise TypeError("SECURITY_MIDDLEWARE_ERROR_INVALID_REQUEST_INSTANCE")

        host_header = request.headers.get("host", "")
        if host_header and not re.match(r"^[a-zA-Z0-9\-\.\:]+$", host_header):
            logger.error("MALFORMED_HOST_HEADER_REJECTED: %r", host_header)
            return Response(
                content='{"error":"CRITICAL_SECURITY_VIOLATION_MALFORMED_HOST_HEADER"}',
                status_code=400,
                media_type="application/json",
            )

        response: Response = await call_next(request)

        if not isinstance(response, Response):
            logger.error("SECURITY_MIDDLEWARE_INVALID_RESPONSE_INSTANCE")
            raise TypeError("SECURITY_MIDDLEWARE_ERROR_INVALID_RESPONSE_INSTANCE")

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'; object-src 'none';"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"

        return response


def validate_env() -> List[str]:
    required_vars = [
        "FASTRA_DT_SECRET_KEY",
        "FASTRA_DT_API_KEY",
        "FASTRA_DT_ADMIN_PASSWORD",
        "FASTRA_DT_QS_PASSWORD",
        "FASTRA_DT_VIEWER_PASSWORD",
    ]

    missing_vars = []
    weak_vars = []

    for var in required_vars:
        value = os.getenv(var)
        if not value or not value.strip():
            missing_vars.append(var)
            continue

        clean_value = value.strip()
        if len(clean_value) < 12:
            weak_vars.append(var)
        if re.match(r"^(admin|qs|viewer)?123$|^secret$|^password$", clean_value, re.IGNORECASE):
            weak_vars.append(var)

    errors: List[str] = []
    if missing_vars:
        errors.append(f"MISSING_VARIABLES: {sorted(missing_vars)}")
    if weak_vars:
        errors.append(f"WEAK_VARIABLES: {sorted(weak_vars)}")

    if errors:
        logger.error("ENVIRONMENT_VALIDATION_FAILED: %s", "; ".join(errors))

    return errors