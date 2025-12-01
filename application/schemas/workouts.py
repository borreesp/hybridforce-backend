from typing import List, Optional

from pydantic import Field

from domain.models.enums import AthleteLevel, EnergyDomain, IntensityLevel, PhysicalCapacity, MuscleGroup, HyroxStation
from .workout_blocks import WorkoutBlockSchema
from .base import ORMModel


class WorkoutLevelTimeSchema(ORMModel):
    athlete_level: AthleteLevel
    time_minutes: float
    time_range: str


class WorkoutCapacitySchema(ORMModel):
    capacity: PhysicalCapacity
    value: int
    note: str


class WorkoutHyroxStationSchema(ORMModel):
    station: HyroxStation
    transfer_pct: int


class WorkoutBase(ORMModel):
    parent_workout_id: Optional[int] = None
    version: Optional[int] = 1
    is_active: Optional[bool] = True
    title: str
    description: str
    domain: EnergyDomain
    intensity: IntensityLevel
    hyrox_transfer: IntensityLevel
    wod_type: str
    volume_total: str
    work_rest_ratio: str
    dominant_stimulus: str
    load_type: str
    estimated_difficulty: float
    main_muscle_chain: str
    extra_attributes_json: Optional[dict] = None
    athlete_profile_desc: str
    target_athlete_desc: str
    session_load: str
    session_feel: str
    official_tag: Optional[str] = None
    pacing_tip: Optional[str] = None
    pacing_detail: Optional[str] = None
    break_tip: Optional[str] = None
    rx_variant: Optional[str] = None
    scaled_variant: Optional[str] = None
    ai_observation: Optional[str] = None
    avg_time_seconds: Optional[int] = None
    avg_rating: Optional[float] = None
    avg_difficulty: Optional[float] = None
    rating_count: Optional[int] = None


class WorkoutCreate(WorkoutBase):
    level_times: List[WorkoutLevelTimeSchema] = Field(default_factory=list)
    capacities: List[WorkoutCapacitySchema] = Field(default_factory=list)
    hyrox_stations: List[WorkoutHyroxStationSchema] = Field(default_factory=list)
    muscles: List[MuscleGroup] = Field(default_factory=list)
    equipment_ids: List[int] = Field(default_factory=list)
    similar_workout_ids: List[int] = Field(default_factory=list)


class WorkoutUpdate(ORMModel):
    parent_workout_id: Optional[int] = None
    version: Optional[int] = None
    is_active: Optional[bool] = None
    title: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[EnergyDomain] = None
    intensity: Optional[IntensityLevel] = None
    hyrox_transfer: Optional[IntensityLevel] = None
    wod_type: Optional[str] = None
    volume_total: Optional[str] = None
    work_rest_ratio: Optional[str] = None
    dominant_stimulus: Optional[str] = None
    load_type: Optional[str] = None
    estimated_difficulty: Optional[float] = None
    main_muscle_chain: Optional[str] = None
    extra_attributes_json: Optional[dict] = None
    athlete_profile_desc: Optional[str] = None
    target_athlete_desc: Optional[str] = None
    session_load: Optional[str] = None
    session_feel: Optional[str] = None
    official_tag: Optional[str] = None
    pacing_tip: Optional[str] = None
    pacing_detail: Optional[str] = None
    break_tip: Optional[str] = None
    rx_variant: Optional[str] = None
    scaled_variant: Optional[str] = None
    ai_observation: Optional[str] = None
    avg_time_seconds: Optional[int] = None
    avg_rating: Optional[float] = None
    avg_difficulty: Optional[float] = None
    rating_count: Optional[int] = None
    level_times: Optional[List[WorkoutLevelTimeSchema]] = None
    capacities: Optional[List[WorkoutCapacitySchema]] = None
    hyrox_stations: Optional[List[WorkoutHyroxStationSchema]] = None
    muscles: Optional[List[MuscleGroup]] = None
    equipment_ids: Optional[List[int]] = None
    similar_workout_ids: Optional[List[int]] = None


class WorkoutRead(WorkoutBase):
    id: int
    level_times: List[WorkoutLevelTimeSchema] = Field(default_factory=list)
    capacities: List[WorkoutCapacitySchema] = Field(default_factory=list)
    hyrox_stations: List[WorkoutHyroxStationSchema] = Field(default_factory=list)
    muscles: List[MuscleGroup] = Field(default_factory=list)
    equipment_ids: List[int] = Field(default_factory=list)
    similar_workout_ids: List[int] = Field(default_factory=list)
    blocks: List[WorkoutBlockSchema] = Field(default_factory=list)


class WorkoutFilter(ORMModel):
    level: Optional[AthleteLevel] = None
    domain: Optional[EnergyDomain] = None
    muscle: Optional[MuscleGroup] = None


class WorkoutAnalysisResponse(ORMModel):
    workout_id: Optional[int] = None
    fatigue_score: float
    hyrox_transfer: float
    capacity_focus: List[dict]
    pacing: dict
    expected_feel: str
    session_load: str


class WorkoutStatsRead(ORMModel):
    workout_id: int
    title: Optional[str] = None
    estimated_difficulty: Optional[float] = None
    avg_time_seconds: Optional[int] = None
    avg_rating: Optional[float] = None
    avg_difficulty: Optional[float] = None
    rating_count: Optional[int] = None
