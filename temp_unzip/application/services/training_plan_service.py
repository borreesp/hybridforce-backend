from typing import Optional

from application.schemas.training_plans import TrainingPlanCreate, TrainingPlanUpdate
from infrastructure.db.models import TrainingPlanORM
from infrastructure.db.repositories import TrainingPlanRepository


class TrainingPlanService:
    def __init__(self, session):
        self.repo = TrainingPlanRepository(session)

    def list(self):
        return self.repo.list()

    def get(self, plan_id: int) -> Optional[TrainingPlanORM]:
        return self.repo.get(plan_id)

    def create(self, data: TrainingPlanCreate):
        days = data.days
        payload = data.model_dump(exclude={"days"})
        plan = self.repo.create(**payload)
        if days:
            day_dicts = [day.model_dump() for day in days]
            self.repo.replace_days(plan, day_dicts)
        return plan

    def update(self, plan_id: int, data: TrainingPlanUpdate):
        plan = self.repo.get(plan_id)
        if not plan:
            return None
        payload = data.model_dump(exclude={"days"}, exclude_none=True)
        if payload:
            plan = self.repo.update(plan, **payload)
        if data.days is not None:
            day_dicts = [day.model_dump() for day in data.days]
            self.repo.replace_days(plan, day_dicts)
        return plan

    def delete(self, plan_id: int):
        plan = self.repo.get(plan_id)
        if not plan:
            return None
        return self.repo.delete(plan)

    def list_days(self, plan_id: int):
        return self.repo.list_days(plan_id)
