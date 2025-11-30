from sqlalchemy.orm import Session

from infrastructure.db.models import UserORM
from .base import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, session: Session):
        super().__init__(session, UserORM)

    def get_by_email(self, email: str):
        return self.session.query(UserORM).filter(UserORM.email == email).first()
