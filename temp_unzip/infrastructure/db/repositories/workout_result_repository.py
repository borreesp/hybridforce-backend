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

    def latest_for_user_workout(self, user_id: int, workout_id: int):
        return (
            self.session.query(WorkoutResultORM)
            .filter(WorkoutResultORM.user_id == user_id, WorkoutResultORM.workout_id == workout_id)
            .order_by(WorkoutResultORM.created_at.desc())
            .first()
        )
