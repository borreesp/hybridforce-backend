from typing import Optional

from application.schemas.equipment import EquipmentCreate, EquipmentUpdate
from infrastructure.db.repositories import EquipmentRepository
from infrastructure.db.models import EquipmentORM


class EquipmentService:
    def __init__(self, session):
        self.repo = EquipmentRepository(session)

    def list(self):
        return self.repo.list()

    def get(self, equipment_id: int) -> Optional[EquipmentORM]:
        return self.repo.get(equipment_id)

    def create(self, data: EquipmentCreate):
        return self.repo.create(**data.model_dump())

    def update(self, equipment_id: int, data: EquipmentUpdate):
        equipment = self.repo.get(equipment_id)
        if not equipment:
            return None
        payload = data.model_dump(exclude_none=True)
        return self.repo.update(equipment, **payload)

    def delete(self, equipment_id: int):
        equipment = self.repo.get(equipment_id)
        if not equipment:
            return None
        return self.repo.delete(equipment)
