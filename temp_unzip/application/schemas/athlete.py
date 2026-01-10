from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel


class CareerSnapshot(BaseModel):
    xp_total: int
    level: int
    progress_pct: float
    next_level: Optional[int] = None
    xp_to_next: Optional[int] = None
    weekly_streak: Optional[int] = None
    updated_at: datetime


class CapacityItem(BaseModel):
    capacity: str
    value: int
    measured_at: datetime


class SkillItem(BaseModel):
    movement: str
    score: float
    measured_at: datetime


class BiometricsItem(BaseModel):
    measured_at: datetime
    hr_rest: Optional[float] = None
    hr_avg: Optional[float] = None
    hr_max: Optional[float] = None
    vo2_est: Optional[float] = None
    hrv: Optional[float] = None
    sleep_hours: Optional[float] = None
    fatigue_score: Optional[float] = None
    recovery_time_hours: Optional[float] = None


class TrainingLoadItem(BaseModel):
    load_date: date
    acute_load: Optional[float] = None
    chronic_load: Optional[float] = None
    load_ratio: Optional[float] = None


class PRItem(BaseModel):
    movement: str
    pr_type: str
    value: float
    unit: Optional[str] = None
    achieved_at: datetime


class AchievementItem(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    xp_reward: float
    icon_url: Optional[str] = None
    unlocked_at: Optional[datetime] = None


class MissionItem(BaseModel):
    id: int
    mission_id: int
    type: str
    title: str
    description: Optional[str] = None
    xp_reward: float
    status: str
    progress_value: float
    target_value: Optional[float] = None
    expires_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class BenchmarkItem(BaseModel):
    capacity: str
    percentile: Optional[float] = None
    level: Optional[int] = None


class AthleteProfileResponse(BaseModel):
    career: CareerSnapshot
    capacities: List[CapacityItem]
    skills: List[SkillItem]
    biometrics: Optional[BiometricsItem] = None
    training_load: List[TrainingLoadItem]
    prs: List[PRItem]
    achievements: List[AchievementItem]
    missions: List[MissionItem]
    benchmarks: List[BenchmarkItem]
