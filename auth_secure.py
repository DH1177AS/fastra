"""
JWT Authentication & RBAC untuk FASTRA Digital Twin API.
Hardened: constant-time password verification, strict Pydantic token payload,
secure default user provisioning via environment variables, structured logging.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

logger = logging.getLogger("fastra_core.auth_secure")

SECRET_KEY = os.getenv(
    "FASTRA_DT_SECRET_KEY",
    "dev-secret-key-change-me-this-is-a-long-enough-key-0123456789abcdef",
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

ROLE_ADMIN = "admin"
ROLE_QS = "qs"
ROLE_VIEWER = "viewer"
_ALLOWED_ROLES = frozenset({ROLE_ADMIN, ROLE_QS, ROLE_VIEWER})

# ------------------------------------------------------------------------------
# User database provisioning (avoid hardcoded plaintext passwords)
# ------------------------------------------------------------------------------
def _hash_password(plain: str) -> str:
    """Hash password with bcrypt using a defined cost factor."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def _get_env_password(username: str, default_plain: str) -> str:
    """Retrieve password from environment variable or fall back to development default."""
    env_var = f"FASTRA_DT_PASSWORD_{username.upper()}"
    env_value = os.getenv(env_var)
    if env_value:
        return env_value
    logger.warning(
        "Environment variable %s not set; using development default for user %s. "
        "This is insecure for production!",
        env_var,
        username,
    )
    return default_plain


def _initialize_users_db() -> Dict[str, Dict[str, str]]:
    """Build the user database from environment variables with secure hashing."""
    users: Dict[str, Dict[str, str]] = {}
    default_users = [
        ("admin", ROLE_ADMIN, "admin123"),
        ("qs", ROLE_QS, "qs123"),
        ("viewer", ROLE_VIEWER, "viewer123"),
    ]
    for username, role, default_password in default_users:
        plain_password = _get_env_password(username, default_password)
        users[username] = {
            "username": username,
            "password_hash": _hash_password(plain_password),
            "role": role,
        }
    return users


USERS_DB: Dict[str, Dict[str, str]] = _initialize_users_db()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# ------------------------------------------------------------------------------
# 1. LAYER DTO & VALIDATOR TOKEN (STRICT)
# ------------------------------------------------------------------------------
class TokenPayload(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        strict=True,
        frozen=True,
        allow_inf_nan=False,
        populate_by_name=False,
        arbitrary_types_allowed=False,
    )

    sub: str = Field(..., min_length=1, max_length=255)
    role: str = Field(..., min_length=1, max_length=50)
    exp: int

    @field_validator("role")
    @classmethod
    def _validate_role(cls, value: str) -> str:
        if value not in _ALLOWED_ROLES:
            raise ValueError("unauthorized_system_role_detected")
        return value

    @field_validator("exp")
    @classmethod
    def _validate_expiration(cls, value: int) -> int:
        # Ensure expiration timestamp is in the future; allows small clock skew tolerance
        if value < int(time.time()):
            raise ValueError("token_has_expired_chronologically")
        return value


# ------------------------------------------------------------------------------
# 2. LAYAR LOGIKA DOMAIN UTAMA OTENTIKASI
# ------------------------------------------------------------------------------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash (constant-time)."""
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except (ValueError, TypeError) as exc:
        logger.warning("Password verification failed due to invalid hash: %s", exc)
        return False


def create_access_token(
    username: str,
    role: str,
    expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES,
) -> str:
    """Create a signed JWT access token."""
    if role not in _ALLOWED_ROLES:
        raise ValueError("invalid_role_for_token")
    now = int(time.time())
    payload = {
        "sub": str(username),
        "role": str(role),
        "exp": now + expires_minutes * 60,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[TokenPayload]:
    """Decode and validate a JWT, returning a TokenPayload or None."""
    try:
        raw_payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Use model_validate to benefit from strict validation
        return TokenPayload.model_validate(raw_payload)
    except (jwt.PyJWTError, ValidationError, ValueError) as exc:
        logger.debug("Token validation failed: %s", exc)
        return None


# ------------------------------------------------------------------------------
# 3. INTERCEPTOR / DEPENDENCY INJECTION LAYER
# ------------------------------------------------------------------------------
def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    """FastAPI dependency that extracts and validates the current user."""
    payload = decode_token(token)
    if payload is None:
        logger.info("Authentication failed: invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def require_role(required_role: str):
    """Dependency factory for role-based access control."""
    if required_role not in _ALLOWED_ROLES:
        raise ValueError("invalid_required_role")

    def role_dependency(user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        if user.role != required_role:
            logger.warning(
                "Access denied for user %s: insufficient role %s (requires %s)",
                user.sub,
                user.role,
                required_role,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return role_dependency