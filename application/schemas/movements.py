from typing import List, Optional

from pydantic import Field

from .base import ORMModel


class MovementMuscleSchema(ORMModel):
    muscle_group: str
    is_primary: bool = True


class MovementBase(ORMModel):
    name: str
    code: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    pattern: Optional[str] = None
    default_load_unit: Optional[str] = None
    default_metric_unit: Optional[str] = None
    supports_reps: Optional[bool] = None
    supports_load: Optional[bool] = None
    supports_distance: Optional[bool] = None
    supports_time: Optional[bool] = None
    supports_calories: Optional[bool] = None
    skill_level: Optional[str] = None
    video_url: Optional[str] = None


class MovementCreate(MovementBase):
    muscles: List[MovementMuscleSchema] = Field(default_factory=list)


class MovementUpdate(ORMModel):
    name: Optional[str] = None
    code: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    pattern: Optional[str] = None
    default_load_unit: Optional[str] = None
    default_metric_unit: Optional[str] = None
    supports_reps: Optional[bool] = None
    supports_load: Optional[bool] = None
    supports_distance: Optional[bool] = None
    supports_time: Optional[bool] = None
    supports_calories: Optional[bool] = None
    skill_level: Optional[str] = None
    video_url: Optional[str] = None
    muscles: Optional[List[MovementMuscleSchema]] = None


class MovementRead(MovementBase):
    id: int
    muscles: List[MovementMuscleSchema] = Field(default_factory=list)
