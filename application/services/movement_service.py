from typing import Optional

from application.schemas.movements import MovementCreate, MovementUpdate
from infrastructure.db.repositories import MovementRepository


class MovementService:
    def __init__(self, session):
        self.repo = MovementRepository(session)

    def list(self):
        return self.repo.list_with_muscles()

    def get(self, movement_id: int):
        return self.repo.get_with_muscles(movement_id)

    def create(self, data: MovementCreate):
        payload = data.model_dump(exclude_none=True)
        muscles = payload.pop("muscles", [])
        movement = self.repo.create(**payload)
        self.repo.upsert_muscles(movement, muscles)
        movement = self.repo.get_with_muscles(movement.id)
        return movement

    def update(self, movement_id: int, data: MovementUpdate) -> Optional[object]:
        movement = self.repo.get(movement_id)
        if not movement:
            return None
        payload = data.model_dump(exclude_none=True)
        muscles = payload.pop("muscles", None)
        movement = self.repo.update(movement, **payload)
        if muscles is not None:
            self.repo.upsert_muscles(movement, muscles)
        return self.repo.get_with_muscles(movement.id)
