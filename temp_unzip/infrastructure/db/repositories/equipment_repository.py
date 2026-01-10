from sqlalchemy.orm import Session

from infrastructure.db.models import EquipmentORM
from .base import BaseRepository


class EquipmentRepository(BaseRepository):
    def __init__(self, session: Session):
        super().__init__(session, EquipmentORM)
