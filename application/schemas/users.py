from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from pydantic import Field

from domain.models.enums import AthleteLevel
from .base import ORMModel


class UserBase(ORMModel):
    name: str
    email: str
    athlete_level: AthleteLevel


class UserCreate(UserBase):
    password: str


class UserUpdate(ORMModel):
    name: Optional[str] = None
    email: Optional[str] = None
    athlete_level: Optional[AthleteLevel] = None
    password: Optional[str] = None


class UserRead(UserBase):
    id: int


class UserProfile(UserRead):
    events: List["EventRead"] = Field(default_factory=list)
    results: List["WorkoutResultRead"] = Field(default_factory=list)


if TYPE_CHECKING:  # pragma: no cover - import cycle guard
    from .events import EventRead
    from .results import WorkoutResultRead


# Import at runtime to satisfy forward refs without cyclic import errors
from .events import EventRead  # noqa: E402
from .results import WorkoutResultRead  # noqa: E402

UserProfile.model_rebuild(_types_namespace={"EventRead": EventRead, "WorkoutResultRead": WorkoutResultRead})
