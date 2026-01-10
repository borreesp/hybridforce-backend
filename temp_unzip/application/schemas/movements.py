from typing import List, Optional

from pydantic import Field

from .base import ORMModel


class MovementMuscleSchema(ORMModel):
    muscle_group: str
    is_primary: bool = True


class MovementBase(ORMModel):
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    default_load_unit: Optional[str] = None
    video_url: Optional[str] = None


class MovementCreate(MovementBase):
    muscles: List[MovementMuscleSchema] = Field(default_factory=list)


class MovementUpdate(ORMModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    default_load_unit: Optional[str] = None
    video_url: Optional[str] = None
    muscles: Optional[List[MovementMuscleSchema]] = None


class MovementRead(MovementBase):
    id: int
    muscles: List[MovementMuscleSchema] = Field(default_factory=list)
