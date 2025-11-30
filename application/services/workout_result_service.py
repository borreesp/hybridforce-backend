from typing import Optional

from application.schemas.results import WorkoutResultCreate, WorkoutResultUpdate
from infrastructure.db.repositories import WorkoutResultRepository, UserRepository, WorkoutRepository
from infrastructure.db.models import WorkoutResultORM


class WorkoutResultService:
    def __init__(self, session):
        self.repo = WorkoutResultRepository(session)
        self.user_repo = UserRepository(session)
        self.workout_repo = WorkoutRepository(session)

    def list(self):
        return self.repo.list()

    def get(self, result_id: int) -> Optional[WorkoutResultORM]:
        return self.repo.get(result_id)

    def create(self, data: WorkoutResultCreate):
        if not self.user_repo.get(data.user_id) or not self.workout_repo.get(data.workout_id):
            return None
        return self.repo.create(**data.model_dump())

    def update(self, result_id: int, data: WorkoutResultUpdate):
        result = self.repo.get(result_id)
        if not result:
            return None
        payload = data.model_dump(exclude_none=True)
        return self.repo.update(result, **payload)

    def delete(self, result_id: int):
        result = self.repo.get(result_id)
        if not result:
            return None
        return self.repo.delete(result)

    def by_workout(self, workout_id: int):
        return self.repo.list_by_workout(workout_id)
