import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import logging
from jose import JWTError, jwt
from passlib.context import CryptContext

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "20"))
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7)))
SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY", SECRET_KEY)

logger = logging.getLogger("auth.security")
if SECRET_KEY == "change-me":
    logger.warning("SECRET_KEY is using default fallback value; set SECRET_KEY in environment")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(password, hashed)
    except Exception:
        return False


def create_token(data: Dict[str, Any], expires_minutes: int, refresh: bool = False) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    key = REFRESH_SECRET_KEY if refresh else SECRET_KEY
    return jwt.encode(to_encode, key, algorithm=ALGORITHM)


def decode_token(token: str, refresh: bool = False) -> Optional[Dict[str, Any]]:
    try:
        key = REFRESH_SECRET_KEY if refresh else SECRET_KEY
        payload = jwt.decode(token, key, algorithms=[ALGORITHM])
        return payload
    except JWTError as exc:
        logger.warning(
            "decode_token failed",
            extra={"refresh": refresh, "error": str(exc), "token_present": bool(token), "token_len": len(token) if token else 0},
        )
        return None
