from __future__ import annotations

from sqlalchemy.orm import Session, joinedload

from infrastructure.db.models import MovementMuscleORM, MovementORM, MuscleGroupORM
from .base import BaseRepository


class MovementRepository(BaseRepository):
    def __init__(self, session: Session):
        super().__init__(session, MovementORM)

    def list(self):
        return self.session.query(MovementORM).options(joinedload(MovementORM.aliases)).all()

    def list_with_muscles(self):
        return (
            self.session.query(MovementORM)
            .options(
                joinedload(MovementORM.muscles).joinedload(MovementMuscleORM.muscle_group),
                joinedload(MovementORM.aliases),
            )
            .all()
        )

    def get_with_muscles(self, movement_id: int):
        return (
            self.session.query(MovementORM)
            .options(
                joinedload(MovementORM.muscles).joinedload(MovementMuscleORM.muscle_group),
                joinedload(MovementORM.aliases),
            )
            .filter(MovementORM.id == movement_id)
            .first()
        )

    def upsert_muscles(self, movement: MovementORM, muscles: list[dict] | None):
        if muscles is None:
            return
        movement.muscles.clear()
        for mm in muscles:
            muscle_code = mm.get("muscle_group")
            if not muscle_code:
                continue
            muscle_row = self.session.query(MuscleGroupORM).filter(MuscleGroupORM.code == muscle_code).first()
            if not muscle_row:
                continue
            movement.muscles.append(
                MovementMuscleORM(movement_id=movement.id, muscle_group_id=muscle_row.id, is_primary=mm.get("is_primary", True))
            )
        self.session.commit()
