from typing import Optional

from application.schemas.auth import LoginRequest, RegisterRequest
from infrastructure.auth.security import (
    hash_password,
    verify_password,
    create_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_MINUTES,
)
from infrastructure.db.models import UserORM
from infrastructure.db.repositories import UserRepository


class AuthService:
    def __init__(self, session):
        self.repo = UserRepository(session)
        self.session = session

    def authenticate(self, data: LoginRequest) -> Optional[UserORM]:
        if len(data.password.encode("utf-8")) > 72:
            return None
        user = self.session.query(UserORM).filter(UserORM.email == data.email.lower()).first()
        if not user:
            return None
        if verify_password(data.password, user.password):
            return user

        if user.password == data.password and len(data.password.encode("utf-8")) <= 72:
            try:
                user.password = hash_password(data.password)
                self.session.commit()
                self.session.refresh(user)
                return user
            except ValueError:
                return None
        return None

    def register(self, data: RegisterRequest) -> Optional[UserORM]:
        existing = self.session.query(UserORM).filter(UserORM.email == data.email.lower()).first()
        if existing:
            return None
        payload = {"name": data.name, "email": data.email.lower(), "password": hash_password(data.password)}
        return self.repo.create(**payload)

    def issue_tokens(self, user: UserORM):
        claims = {"sub": str(user.id), "v": user.token_version}
        access = create_token(claims, ACCESS_TOKEN_EXPIRE_MINUTES, refresh=False)
        refresh = create_token(claims, REFRESH_TOKEN_EXPIRE_MINUTES, refresh=True)
        return access, refresh

    def bump_token_version(self, user: UserORM):
        user.token_version = (user.token_version or 0) + 1
        self.session.commit()
        self.session.refresh(user)
