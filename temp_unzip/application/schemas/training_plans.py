from typing import List, Optional

from pydantic import Field

from .base import ORMModel


class TrainingPlanDayBase(ORMModel):
    day_number: int
    focus: str
    description: str


class TrainingPlanDayRead(TrainingPlanDayBase):
    plan_id: int


class TrainingPlanBase(ORMModel):
    name: str
    description: Optional[str] = None


class TrainingPlanCreate(TrainingPlanBase):
    days: List[TrainingPlanDayBase] = Field(default_factory=list)


class TrainingPlanUpdate(ORMModel):
    name: Optional[str] = None
    description: Optional[str] = None
    days: Optional[List[TrainingPlanDayBase]] = None


class TrainingPlanRead(TrainingPlanBase):
    id: int
    days: List[TrainingPlanDayRead] = Field(default_factory=list)
