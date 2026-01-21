from typing import Optional, List, Literal, Dict

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
    method: Literal["total", "by_blocks"] = "total"
    total_time_sec: Optional[int] = None
    block_times_sec: Optional[List[int]] = None
    segment_times_sec: Optional[Dict[str, float]] = None
    segment_mode: Optional[str] = None
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
