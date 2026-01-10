from typing import List, Optional

from pydantic import Field

from .base import ORMModel
from .movements import MovementRead


class WorkoutBlockMovementSchema(ORMModel):
    id: int
    movement_id: int
    position: int
    reps: Optional[float] = None
    load: Optional[float] = None
    load_unit: Optional[str] = None
    distance_meters: Optional[float] = None
    duration_seconds: Optional[int] = None
    calories: Optional[float] = None
    movement: Optional[MovementRead] = None


class WorkoutBlockSchema(ORMModel):
    id: int
    workout_id: int
    position: int
    block_type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    duration_seconds: Optional[int] = None
    rounds: Optional[int] = None
    notes: Optional[str] = None
    movements: List[WorkoutBlockMovementSchema] = Field(default_factory=list)


class WorkoutStructure(ORMModel):
    blocks: List[WorkoutBlockSchema] = Field(default_factory=list)
