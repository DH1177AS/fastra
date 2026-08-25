"""
JWT Authentication & RBAC untuk FASTRA Digital Twin API.
"""
from __future__ import annotations

import os
import time
from typing import Dict, Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

SECRET_KEY = os.getenv(
    "FASTRA_DT_SECRET_KEY",
    "dev-secret-key-change-me-this-is-a-long-enough-key-0123456789abcdef",
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Role definitions
ROLE_ADMIN = "admin"
ROLE_QS = "qs"
ROLE_VIEWER = "viewer"

# Fake user database (replace with real DB in production)
USERS_DB: Dict[str, Dict[str, str]] = {
    "admin": {
        "username": "admin",
        "password_hash": bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode(),
        "role": ROLE_ADMIN,
    },
    "qs": {
        "username": "qs",
        "password_hash": bcrypt.hashpw(b"qs123", bcrypt.gensalt()).decode(),
        "role": ROLE_QS,
    },
    "viewer": {
        "username": "viewer",
        "password_hash": bcrypt.hashpw(b"viewer123", bcrypt.gensalt()).decode(),
        "role": ROLE_VIEWER,
    },
}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class TokenPayload(BaseModel):
    sub: str
    role: str
    exp: int


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(username: str, role: str, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    expire = int(time.time()) + expires_minutes * 60
    payload = {"sub": username, "role": role, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[TokenPayload]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenPayload(**payload)
    except jwt.PyJWTError:
        return None


def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def require_role(required_role: str):
    """Dependency factory untuk role-based access control."""
    def role_dependency(user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        if user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' tidak diizinkan. Butuh '{required_role}'.",
            )
        return user
    return role_dependency
