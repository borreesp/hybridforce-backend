from sqlalchemy.orm import Session

from infrastructure.db.models import TrainingPlanORM, TrainingPlanDayORM
from .base import BaseRepository


class TrainingPlanRepository(BaseRepository):
    def __init__(self, session: Session):
        super().__init__(session, TrainingPlanORM)

    def list_days(self, plan_id: int):
        return (
            self.session.query(TrainingPlanDayORM)
            .filter(TrainingPlanDayORM.plan_id == plan_id)
            .order_by(TrainingPlanDayORM.day_number)
            .all()
        )

    def replace_days(self, plan: TrainingPlanORM, days: list[dict]):
        plan.days.clear()
        for day in days:
            plan.days.append(
                TrainingPlanDayORM(
                    plan_id=plan.id,
                    day_number=day["day_number"],
                    focus=day["focus"],
                    description=day["description"],
                )
            )
        self.session.commit()
        self.session.refresh(plan)
        return plan
