import logging

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from infrastructure.db.models import UserORM
from infrastructure.db.session import get_session
from .security import decode_token

logger = logging.getLogger("auth.dependencies")


def _extract_token(request: Request) -> str | None:
    return request.cookies.get("access_token")


def get_current_user(
    request: Request,
    session: Session = Depends(get_session),
) -> UserORM:
    token = _extract_token(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload.get("sub")
    token_version = payload.get("v")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = session.get(UserORM, int(user_id))
    if not user or user.token_version != token_version:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    return user


def require_user(user: UserORM = Depends(get_current_user)) -> UserORM:
    return user
