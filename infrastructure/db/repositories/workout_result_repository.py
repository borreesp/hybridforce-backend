from sqlalchemy.orm import Session

from infrastructure.db.models import WorkoutResultORM
from .base import BaseRepository


class WorkoutResultRepository(BaseRepository):
    def __init__(self, session: Session):
        super().__init__(session, WorkoutResultORM)

    def list_by_workout(self, workout_id: int):
        return self.session.query(WorkoutResultORM).filter(WorkoutResultORM.workout_id == workout_id).all()

    def list_by_user(self, user_id: int):
        return self.session.query(WorkoutResultORM).filter(WorkoutResultORM.user_id == user_id).all()
