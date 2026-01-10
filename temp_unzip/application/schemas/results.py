from typing import Optional

from .base import ORMModel


class WorkoutResultBase(ORMModel):
    workout_id: int
    user_id: int
    time_seconds: int
    difficulty: Optional[int] = None
    rating: Optional[int] = None
    comment: Optional[str] = None


class WorkoutResultCreate(WorkoutResultBase):
    pass


class WorkoutResultUpdate(ORMModel):
    time_seconds: Optional[int] = None
    difficulty: Optional[int] = None
    rating: Optional[int] = None
    comment: Optional[str] = None


class WorkoutResultRead(WorkoutResultBase):
    id: int


class WorkoutResultSubmit(ORMModel):
    time_seconds: int
    difficulty: Optional[int] = None
    rating: Optional[int] = None
    comment: Optional[str] = None


class WorkoutResultWithXp(ORMModel):
    result: WorkoutResultRead
    xp_awarded: int
    xp_total: int
    level: int
    progress_pct: float
    achievements_unlocked: list[str]
    missions_completed: list[str]
