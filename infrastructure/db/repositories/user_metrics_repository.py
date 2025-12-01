from sqlalchemy.orm import Session

from infrastructure.db.models import UserCapacityProfileORM, UserTrainingLoadORM, PhysicalCapacityORM
from .base import BaseRepository


class UserTrainingLoadRepository(BaseRepository):
    def __init__(self, session: Session):
        super().__init__(session, UserTrainingLoadORM)

    def list_for_user(self, user_id: int):
        return (
            self.session.query(UserTrainingLoadORM)
            .filter(UserTrainingLoadORM.user_id == user_id)
            .order_by(UserTrainingLoadORM.load_date.desc())
            .all()
        )


class UserCapacityProfileRepository(BaseRepository):
    def __init__(self, session: Session):
        super().__init__(session, UserCapacityProfileORM)

    def list_for_user(self, user_id: int):
        return (
            self.session.query(UserCapacityProfileORM)
            .join(PhysicalCapacityORM, PhysicalCapacityORM.id == UserCapacityProfileORM.capacity_id)
            .filter(UserCapacityProfileORM.user_id == user_id)
            .order_by(UserCapacityProfileORM.measured_at.desc())
            .all()
        )
