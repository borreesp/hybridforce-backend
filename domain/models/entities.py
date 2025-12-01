from dataclasses import dataclass, field
from typing import Optional, List

from .enums import (
    AthleteLevel,
    EnergyDomain,
    IntensityLevel,
    PhysicalCapacity,
    MuscleGroup,
    HyroxStation,
)


@dataclass
class User:
    name: str
    email: str
    password: str
    athlete_level: AthleteLevel
    id: Optional[int] = None


@dataclass
class WorkoutLevelTime:
    workout_id: int
    athlete_level: AthleteLevel
    time_minutes: float
    time_range: str


@dataclass
class WorkoutCapacity:
    workout_id: int
    capacity: PhysicalCapacity
    value: int
    note: str


@dataclass
class WorkoutHyroxStation:
    workout_id: int
    station: HyroxStation
    transfer_pct: int


@dataclass
class WorkoutMuscle:
    workout_id: int
    muscle: MuscleGroup


@dataclass
class Equipment:
    name: str
    description: str
    price: float
    image_url: Optional[str] = None
    category: Optional[str] = None
    id: Optional[int] = None


@dataclass
class WorkoutEquipment:
    workout_id: int
    equipment_id: int


@dataclass
class Workout:
    title: str
    description: str
    domain: EnergyDomain | str | None
    intensity: IntensityLevel | str | None
    hyrox_transfer: IntensityLevel | str | None
    wod_type: str
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
    id: Optional[int] = None
    parent_workout_id: Optional[int] = None
    version: Optional[int] = 1
    is_active: Optional[bool] = True
    level_times: List[WorkoutLevelTime] = field(default_factory=list)
    capacities: List[WorkoutCapacity] = field(default_factory=list)
    hyrox_stations: List[WorkoutHyroxStation] = field(default_factory=list)
    muscles: List[WorkoutMuscle] = field(default_factory=list)
    equipment: List[WorkoutEquipment] = field(default_factory=list)
    blocks: List["WorkoutBlock"] = field(default_factory=list)


@dataclass
class TrainingPlanDay:
    plan_id: int
    day_number: int
    focus: str
    description: str


@dataclass
class TrainingPlan:
    name: str
    description: Optional[str] = None
    id: Optional[int] = None
    days: List[TrainingPlanDay] = field(default_factory=list)


@dataclass
class Event:
    name: str
    date: str
    location: str
    type: Optional[str] = None
    id: Optional[int] = None


@dataclass
class UserEvent:
    user_id: int
    event_id: int


@dataclass
class WorkoutResult:
    workout_id: int
    user_id: int
    time_seconds: int
    difficulty: Optional[int] = None
    rating: Optional[int] = None
    comment: Optional[str] = None
    id: Optional[int] = None


@dataclass
class SimilarWorkout:
    workout_id: int
    similar_workout_id: int


@dataclass
class MovementMuscle:
    movement_id: int
    muscle_group: MuscleGroup
    is_primary: bool


@dataclass
class Movement:
    name: str
    category: Optional[str]
    description: Optional[str]
    default_load_unit: Optional[str]
    video_url: Optional[str]
    id: Optional[int] = None
    muscles: List[MovementMuscle] = field(default_factory=list)


@dataclass
class WorkoutBlockMovement:
    movement_id: int
    position: int
    reps: Optional[float] = None
    load: Optional[float] = None
    load_unit: Optional[str] = None
    distance_meters: Optional[float] = None
    duration_seconds: Optional[int] = None
    calories: Optional[float] = None
    id: Optional[int] = None
    movement: Optional[Movement] = None


@dataclass
class WorkoutBlock:
    workout_id: int
    position: int
    block_type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    duration_seconds: Optional[int] = None
    rounds: Optional[int] = None
    notes: Optional[str] = None
    id: Optional[int] = None
    movements: List[WorkoutBlockMovement] = field(default_factory=list)


@dataclass
class UserTrainingLoad:
    user_id: int
    load_date: str
    acute_load: Optional[float] = None
    chronic_load: Optional[float] = None
    load_ratio: Optional[float] = None
    notes: Optional[str] = None
    id: Optional[int] = None


@dataclass
class UserCapacityProfile:
    user_id: int
    capacity_id: int
    value: int
    measured_at: str
    id: Optional[int] = None
