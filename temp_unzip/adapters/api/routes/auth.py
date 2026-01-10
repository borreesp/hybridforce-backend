from datetime import datetime, timedelta
from typing import Dict
import os

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from application.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, AuthUser, RefreshResponse, LogoutResponse
from application.services.auth_service import AuthService
from infrastructure.auth.dependencies import get_current_user
from infrastructure.auth.security import decode_token
from infrastructure.db.session import get_session
from infrastructure.db.models import UserORM

router = APIRouter()

_login_attempts: Dict[str, list[datetime]] = {}
MAX_ATTEMPTS = 5
WINDOW_MINUTES = 10


def _prune_attempts(key: str):
    cutoff = datetime.utcnow() - timedelta(minutes=WINDOW_MINUTES)
    _login_attempts[key] = [ts for ts in _login_attempts.get(key, []) if ts > cutoff]


def _register_failure(key: str):
    _prune_attempts(key)
    attempts = _login_attempts.get(key, [])
    attempts.append(datetime.utcnow())
    _login_attempts[key] = attempts


def _is_rate_limited(key: str) -> bool:
    _prune_attempts(key)
    return len(_login_attempts.get(key, [])) >= MAX_ATTEMPTS


def _cookie_params():
    secure_env = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    domain_env = os.getenv("COOKIE_DOMAIN")
    domain = None if domain_env in [None, "", "localhost", "127.0.0.1"] else domain_env
    samesite_env = os.getenv("COOKIE_SAMESITE", "lax").lower()
    samesite = samesite_env if samesite_env in {"lax", "strict", "none"} else "lax"
    if samesite == "none" and not secure_env:
        samesite = "lax"
    return {
        "httponly": True,
        "secure": secure_env,
        "samesite": samesite,
        "domain": domain,
        "path": "/",
    }


def _set_auth_cookies(response: Response, access: str, refresh: str):
    params = _cookie_params()
    response.set_cookie("access_token", access, max_age=60 * 20, **params)
    response.set_cookie("refresh_token", refresh, max_age=60 * 60 * 24 * 7, **params)


def _clear_auth_cookies(response: Response):
    params = _cookie_params()
    response.delete_cookie("access_token", **params)
    response.delete_cookie("refresh_token", **params)


@router.post("/login", response_model=AuthResponse)
def login(request: Request, payload: LoginRequest, response: Response, session: Session = Depends(get_session)):
    client_ip = request.client.host if request.client else "unknown"
    key = f"{client_ip}:{payload.email.lower()}"
    if _is_rate_limited(key):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many attempts, try later")

    service = AuthService(session)
    user = service.authenticate(payload)
    if not user:
        _register_failure(key)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access, refresh = service.issue_tokens(user)
    _set_auth_cookies(response, access, refresh)
    return AuthResponse(user=AuthUser(id=user.id, name=user.name, email=user.email), tokens=None)


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(request: Request, payload: RegisterRequest, response: Response, session: Session = Depends(get_session)):
    service = AuthService(session)
    user = service.register(payload)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")

    access, refresh = service.issue_tokens(user)
    _set_auth_cookies(response, access, refresh)
    return AuthResponse(user=AuthUser(id=user.id, name=user.name, email=user.email), tokens=None)


@router.post("/refresh", response_model=RefreshResponse)
def refresh_token(request: Request, response: Response, session: Session = Depends(get_session)):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")

    payload = decode_token(token, refresh=True)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = session.get(UserORM, int(payload["sub"]))
    if not user or user.token_version != payload.get("v"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    service = AuthService(session)
    access, refresh = service.issue_tokens(user)
    _set_auth_cookies(response, access, refresh)
    return RefreshResponse(access_token=access)


@router.post("/logout", response_model=LogoutResponse)
def logout(response: Response, user: UserORM = Depends(get_current_user), session: Session = Depends(get_session)):
    service = AuthService(session)
    service.bump_token_version(user)
    _clear_auth_cookies(response)
    return LogoutResponse()


@router.get("/me", response_model=AuthResponse)
def me(user: UserORM = Depends(get_current_user)):
    return AuthResponse(user=AuthUser(id=user.id, name=user.name, email=user.email), tokens=None)
