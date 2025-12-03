"""
Simple authentication helpers for Audio2txt Enterprise
Provides Basic Auth fallback and JWT-like bearer token issuing
"""
from datetime import datetime, timedelta
import secrets
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials, HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordRequestForm

from packages.core.audio2txt.utils.config import Config

config = Config()
security_basic = HTTPBasic(auto_error=False)
security_bearer = HTTPBearer(auto_error=False)

_TOKEN_STORE: dict[str, dict[str, str]] = {}


def _verify_basic(credentials: HTTPBasicCredentials) -> bool:
    if not credentials:
        return False
    return credentials.username == config.admin_username and credentials.password == config.admin_password


def create_access_token(username: str) -> dict[str, str]:
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(minutes=config.jwt_expire_minutes)
    _TOKEN_STORE[token] = {"username": username, "expires": expires.isoformat()}
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": config.jwt_expire_minutes * 60,
    }


def validate_token(token: str) -> Optional[str]:
    payload = _TOKEN_STORE.get(token)
    if not payload:
        return None
    expires = datetime.fromisoformat(payload["expires"])
    if datetime.utcnow() > expires:
        del _TOKEN_STORE[token]
        return None
    return payload["username"]


def get_current_username(
    basic: HTTPBasicCredentials = Depends(security_basic),
    bearer: HTTPAuthorizationCredentials = Depends(security_bearer),
):
    if bearer and bearer.credentials:
        username = validate_token(bearer.credentials)
        if username:
            return username
    if basic and _verify_basic(basic):
        return basic.username
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def login(form_data: OAuth2PasswordRequestForm = Depends()):
    credentials = HTTPBasicCredentials(username=form_data.username, password=form_data.password)
    if not _verify_basic(credentials):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return create_access_token(credentials.username)
