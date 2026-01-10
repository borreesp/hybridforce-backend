from typing import Optional

from .base import ORMModel


class EquipmentBase(ORMModel):
    name: str
    description: str
    price: float
    image_url: Optional[str] = None
    category: Optional[str] = None


class EquipmentCreate(EquipmentBase):
    pass


class EquipmentUpdate(ORMModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    category: Optional[str] = None


class EquipmentRead(EquipmentBase):
    id: int
