from datetime import date, datetime
from typing import List, Optional

from pydantic import Field

from .base import ORMModel


class UserTrainingLoadRead(ORMModel):
    id: int
    user_id: int
    load_date: date
    acute_load: Optional[float] = None
    chronic_load: Optional[float] = None
    load_ratio: Optional[float] = None
    notes: Optional[str] = None


class UserCapacityProfileRead(ORMModel):
    id: int
    user_id: int
    capacity_code: str
    capacity_name: Optional[str] = None
    value: int
    measured_at: datetime


class UserCapacityProfileResponse(ORMModel):
    user_id: int
    capacities: List[UserCapacityProfileRead] = Field(default_factory=list)
