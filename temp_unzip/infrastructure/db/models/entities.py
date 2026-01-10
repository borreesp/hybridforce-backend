from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from infrastructure.db.session import Base


class AthleteLevelORM(Base):
    __tablename__ = "athlete_levels"
    __table_args__ = (UniqueConstraint("code", name="uq_athlete_levels_code"), Index("ix_athlete_levels_sort", "sort_order"))

    id = Column(Integer, primary_key=True)
    code = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    min_xp = Column(Integer, nullable=True)
    max_xp = Column(Integer, nullable=True)
    sort_order = Column(Integer, nullable=True)

    users = relationship("UserORM", back_populates="athlete_level")
    workout_level_times = relationship("WorkoutLevelTimeORM", back_populates="athlete_level")
    workout_stats_by_level = relationship("WorkoutStatsByLevelORM", back_populates="athlete_level")
    movement_benchmarks = relationship("MovementBenchmarkORM", back_populates="athlete_level")
    capacity_benchmarks = relationship("GlobalCapacityBenchmarkORM", back_populates="athlete_level")


class IntensityLevelORM(Base):
    __tablename__ = "intensity_levels"
    __table_args__ = (UniqueConstraint("code", name="uq_intensity_levels_code"), Index("ix_intensity_levels_sort", "sort_order"))

    id = Column(Integer, primary_key=True)
    code = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    sort_order = Column(Integer, nullable=True)

    workouts = relationship(
        "WorkoutORM",
        foreign_keys="[WorkoutORM.intensity_level_id]",
        back_populates="intensity_level",
        overlaps="hyrox_transfer_level",
    )
    hyrox_transfer_workouts = relationship(
        "WorkoutORM",
        foreign_keys="[WorkoutORM.hyrox_transfer_level_id]",
        back_populates="hyrox_transfer_level",
        overlaps="intensity_level",
    )


class EnergyDomainORM(Base):
    __tablename__ = "energy_domains"
    __table_args__ = (UniqueConstraint("code", name="uq_energy_domains_code"),)

    id = Column(Integer, primary_key=True)
    code = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    workouts = relationship("WorkoutORM", back_populates="domain")


class PhysicalCapacityORM(Base):
    __tablename__ = "physical_capacities"
    __table_args__ = (UniqueConstraint("code", name="uq_physical_capacities_code"),)

    id = Column(Integer, primary_key=True)
    code = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    benchmarks = relationship("GlobalCapacityBenchmarkORM", back_populates="capacity", cascade="all, delete-orphan")


class MuscleGroupORM(Base):
    __tablename__ = "muscle_groups"
    __table_args__ = (UniqueConstraint("code", name="uq_muscle_groups_code"),)

    id = Column(Integer, primary_key=True)
    code = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)


class HyroxStationORM(Base):
    __tablename__ = "hyrox_stations"
    __table_args__ = (UniqueConstraint("code", name="uq_hyrox_stations_code"),)

    id = Column(Integer, primary_key=True)
    code = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)


class UserORM(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="uq_users_email"),)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, index=True)
    password = Column(String(100), nullable=False)
    athlete_level_id = Column(Integer, ForeignKey("athlete_levels.id"), nullable=True)
    token_version = Column(Integer, nullable=False, default=0, server_default="0")

    athlete_level = relationship("AthleteLevelORM", back_populates="users")
    results = relationship("WorkoutResultORM", back_populates="user", cascade="all, delete-orphan")
    events = relationship("UserEventORM", back_populates="user", cascade="all, delete-orphan")
    training_loads = relationship("UserTrainingLoadORM", back_populates="user", cascade="all, delete-orphan")
    capacity_profiles = relationship("UserCapacityProfileORM", back_populates="user", cascade="all, delete-orphan")
    progress = relationship("UserProgressORM", back_populates="user", cascade="all, delete-orphan", uselist=False)
    skills = relationship("UserSkillORM", back_populates="user", cascade="all, delete-orphan")
    biometrics = relationship("UserBiometricORM", back_populates="user", cascade="all, delete-orphan")
    prs = relationship("UserPROM", back_populates="user", cascade="all, delete-orphan")
    executions = relationship("WorkoutExecutionORM", back_populates="user", cascade="all, delete-orphan")
    achievements = relationship("UserAchievementORM", back_populates="user", cascade="all, delete-orphan")
    missions = relationship("UserMissionORM", back_populates="user", cascade="all, delete-orphan")


class EventORM(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    date = Column(Date, nullable=False)
    location = Column(String(100), nullable=False)
    type = Column(String(50), nullable=True)

    participants = relationship("UserEventORM", back_populates="event", cascade="all, delete-orphan")


class UserEventORM(Base):
    __tablename__ = "user_event"
    __table_args__ = (UniqueConstraint("user_id", "event_id", name="uq_user_event"),)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), primary_key=True, nullable=False)

    user = relationship("UserORM", back_populates="events")
    event = relationship("EventORM", back_populates="participants")


class UserTrainingLoadORM(Base):
    __tablename__ = "user_training_load"
    __table_args__ = (
        UniqueConstraint("user_id", "load_date", name="uq_user_load_date"),
        Index("ix_user_training_load_user", "user_id"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    load_date = Column(Date, nullable=False)
    acute_load = Column(Numeric(8, 2), nullable=True)
    chronic_load = Column(Numeric(8, 2), nullable=True)
    load_ratio = Column(Numeric(5, 2), nullable=True)
    notes = Column(Text, nullable=True)

    user = relationship("UserORM", back_populates="training_loads")


class UserCapacityProfileORM(Base):
    __tablename__ = "user_capacity_profile"
    __table_args__ = (
        UniqueConstraint("user_id", "capacity_id", "measured_at", name="uq_user_capacity_measured"),
        Index("ix_user_capacity_user_capacity", "user_id", "capacity_id"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    capacity_id = Column(Integer, ForeignKey("physical_capacities.id", ondelete="CASCADE"), nullable=False)
    value = Column(SmallInteger, nullable=False)
    measured_at = Column(DateTime(timezone=False), nullable=False)

    user = relationship("UserORM", back_populates="capacity_profiles")
    capacity = relationship("PhysicalCapacityORM")


class UserProgressORM(Base):
    __tablename__ = "user_progress"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    xp_total = Column(Integer, nullable=False, default=0, server_default="0")
    level = Column(Integer, nullable=False, default=1, server_default="1")
    progress_pct = Column(Numeric(5, 2), nullable=False, default=0, server_default="0")
    updated_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())

    user = relationship("UserORM", back_populates="progress")


class UserSkillORM(Base):
    __tablename__ = "user_skills"
    __table_args__ = (Index("ix_user_skills_user", "user_id"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    movement_id = Column(Integer, ForeignKey("movements.id", ondelete="CASCADE"), nullable=False)
    skill_score = Column(Numeric(5, 2), nullable=False)
    note = Column(Text, nullable=True)
    measured_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())

    user = relationship("UserORM", back_populates="skills")
    movement = relationship("MovementORM")


class UserBiometricORM(Base):
    __tablename__ = "user_biometrics"
    __table_args__ = (Index("ix_user_biometrics_user", "user_id"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    measured_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())
    hr_rest = Column(Numeric(6, 2), nullable=True)
    hr_avg = Column(Numeric(6, 2), nullable=True)
    hr_max = Column(Numeric(6, 2), nullable=True)
    vo2_est = Column(Numeric(6, 2), nullable=True)
    hrv = Column(Numeric(6, 2), nullable=True)
    sleep_hours = Column(Numeric(4, 2), nullable=True)
    fatigue_score = Column(Numeric(4, 2), nullable=True)
    recovery_time_hours = Column(Numeric(6, 2), nullable=True)

    user = relationship("UserORM", back_populates="biometrics")


class UserPROM(Base):
    __tablename__ = "user_pr"
    __table_args__ = (
        UniqueConstraint("user_id", "movement_id", "pr_type", name="uq_user_pr_unique"),
        Index("ix_user_pr_user", "user_id"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    movement_id = Column(Integer, ForeignKey("movements.id", ondelete="CASCADE"), nullable=False)
    pr_type = Column(String(30), nullable=False)
    value = Column(Numeric(10, 2), nullable=False)
    unit = Column(String(20), nullable=True)
    achieved_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())

    user = relationship("UserORM", back_populates="prs")
    movement = relationship("MovementORM")


class WorkoutORM(Base):
    __tablename__ = "workouts"
    __table_args__ = (
        UniqueConstraint("parent_workout_id", "version", name="uq_workouts_version"),
        Index("ix_workouts_parent", "parent_workout_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    parent_workout_id = Column(Integer, ForeignKey("workouts.id", ondelete="SET NULL"), nullable=True)
    version = Column(SmallInteger, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    domain_id = Column(Integer, ForeignKey("energy_domains.id"), nullable=True)
    intensity_level_id = Column(Integer, ForeignKey("intensity_levels.id"), nullable=True)
    hyrox_transfer_level_id = Column(Integer, ForeignKey("intensity_levels.id"), nullable=True)
    wod_type = Column(String(100), nullable=False)
    official_tag = Column(String(50), nullable=True)
    main_muscle_group_id = Column(Integer, ForeignKey("muscle_groups.id"), nullable=True)
    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now(), onupdate=func.now())

    parent = relationship("WorkoutORM", remote_side=[id])
    domain = relationship("EnergyDomainORM", back_populates="workouts")
    intensity_level = relationship(
        "IntensityLevelORM",
        foreign_keys=[intensity_level_id],
        back_populates="workouts",
        overlaps="hyrox_transfer_workouts",
    )
    hyrox_transfer_level = relationship(
        "IntensityLevelORM",
        foreign_keys=[hyrox_transfer_level_id],
        back_populates="hyrox_transfer_workouts",
        overlaps="intensity_level",
    )
    main_muscle_group = relationship("MuscleGroupORM")
    metadata_rel = relationship(
        "WorkoutMetadataORM", back_populates="workout", cascade="all, delete-orphan", uselist=False
    )
    stats = relationship("WorkoutStatsORM", back_populates="workout", cascade="all, delete-orphan", uselist=False)
    stats_by_level = relationship("WorkoutStatsByLevelORM", back_populates="workout", cascade="all, delete-orphan")
    global_performance = relationship("GlobalPerformanceDataORM", back_populates="workout", cascade="all, delete-orphan")
    level_times = relationship("WorkoutLevelTimeORM", back_populates="workout", cascade="all, delete-orphan")
    capacities = relationship("WorkoutCapacityORM", back_populates="workout", cascade="all, delete-orphan")
    hyrox_stations = relationship("WorkoutHyroxStationORM", back_populates="workout", cascade="all, delete-orphan")
    muscles = relationship("WorkoutMuscleORM", back_populates="workout", cascade="all, delete-orphan")
    equipment_links = relationship("WorkoutEquipmentORM", back_populates="workout", cascade="all, delete-orphan")
    results = relationship("WorkoutResultORM", back_populates="workout", cascade="all, delete-orphan")
    executions = relationship("WorkoutExecutionORM", back_populates="workout", cascade="all, delete-orphan")
    similar_from = relationship(
        "SimilarWorkoutORM",
        foreign_keys="SimilarWorkoutORM.workout_id",
        back_populates="workout",
        cascade="all, delete-orphan",
    )
    similar_to = relationship(
        "SimilarWorkoutORM",
        foreign_keys="SimilarWorkoutORM.similar_workout_id",
        back_populates="similar_workout",
        cascade="all, delete-orphan",
    )
    blocks = relationship("WorkoutBlockORM", back_populates="workout", cascade="all, delete-orphan")


class WorkoutMetadataORM(Base):
    __tablename__ = "workout_metadata"
    __table_args__ = (UniqueConstraint("workout_id", name="uq_workout_metadata_id"),)

    workout_id = Column(Integer, ForeignKey("workouts.id", ondelete="CASCADE"), primary_key=True)
    volume_total = Column(Text, nullable=True)
    work_rest_ratio = Column(Text, nullable=True)
    dominant_stimulus = Column(Text, nullable=True)
    load_type = Column(Text, nullable=True)
    athlete_profile_desc = Column(Text, nullable=True)
    target_athlete_desc = Column(Text, nullable=True)
    pacing_tip = Column(Text, nullable=True)
    pacing_detail = Column(Text, nullable=True)
    break_tip = Column(Text, nullable=True)
    rx_variant = Column(Text, nullable=True)
    scaled_variant = Column(Text, nullable=True)
    ai_observation = Column(Text, nullable=True)
    session_load = Column(Text, nullable=True)
    session_feel = Column(Text, nullable=True)
    extra_attributes_json = Column(JSONB, nullable=True)

    workout = relationship("WorkoutORM", back_populates="metadata_rel")


class WorkoutStatsORM(Base):
    __tablename__ = "workout_stats"
    __table_args__ = (UniqueConstraint("workout_id", name="uq_workout_stats_id"),)

    workout_id = Column(Integer, ForeignKey("workouts.id", ondelete="CASCADE"), primary_key=True)
    estimated_difficulty = Column(Numeric(3, 1), nullable=True)
    avg_time_seconds = Column(SmallInteger, nullable=True)
    avg_rating = Column(Numeric(3, 2), nullable=True)
    avg_difficulty = Column(Numeric(3, 1), nullable=True)
    rating_count = Column(Integer, nullable=True)

    workout = relationship("WorkoutORM", back_populates="stats")


class WorkoutLevelTimeORM(Base):
    __tablename__ = "workout_level_time"
    __table_args__ = (UniqueConstraint("workout_id", "athlete_level_id", name="uq_workout_level"),)

    workout_id = Column(Integer, ForeignKey("workouts.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    athlete_level_id = Column(Integer, ForeignKey("athlete_levels.id"), primary_key=True, nullable=False)
    time_minutes = Column(Numeric(4, 1), nullable=False)
    time_range = Column(String(20), nullable=False)

    workout = relationship("WorkoutORM", back_populates="level_times")
    athlete_level = relationship("AthleteLevelORM")


class WorkoutCapacityORM(Base):
    __tablename__ = "workout_capacity"
    __table_args__ = (UniqueConstraint("workout_id", "capacity_id", name="uq_workout_capacity"),)

    workout_id = Column(Integer, ForeignKey("workouts.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    capacity_id = Column(Integer, ForeignKey("physical_capacities.id"), primary_key=True, nullable=False)
    value = Column(SmallInteger, nullable=False)
    note = Column(Text, nullable=False)

    workout = relationship("WorkoutORM", back_populates="capacities")
    capacity = relationship("PhysicalCapacityORM")


class WorkoutHyroxStationORM(Base):
    __tablename__ = "workout_hyrox_station"
    __table_args__ = (UniqueConstraint("workout_id", "station_id", name="uq_workout_station"),)

    workout_id = Column(Integer, ForeignKey("workouts.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    station_id = Column(Integer, ForeignKey("hyrox_stations.id"), primary_key=True, nullable=False)
    transfer_pct = Column(SmallInteger, nullable=False)

    workout = relationship("WorkoutORM", back_populates="hyrox_stations")
    station = relationship("HyroxStationORM")


class WorkoutMuscleORM(Base):
    __tablename__ = "workout_muscle"
    __table_args__ = (UniqueConstraint("workout_id", "muscle_group_id", name="uq_workout_muscle"),)

    workout_id = Column(Integer, ForeignKey("workouts.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    muscle_group_id = Column(Integer, ForeignKey("muscle_groups.id"), primary_key=True, nullable=False)

    workout = relationship("WorkoutORM", back_populates="muscles")
    muscle_group = relationship("MuscleGroupORM")


class EquipmentORM(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Numeric(6, 2), nullable=False)
    image_url = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)

    workouts = relationship("WorkoutEquipmentORM", back_populates="equipment", cascade="all, delete-orphan")


class WorkoutEquipmentORM(Base):
    __tablename__ = "workout_equipment"
    __table_args__ = (UniqueConstraint("workout_id", "equipment_id", name="uq_workout_equipment"),)

    workout_id = Column(Integer, ForeignKey("workouts.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    equipment_id = Column(Integer, ForeignKey("equipment.id", ondelete="CASCADE"), primary_key=True, nullable=False)

    workout = relationship("WorkoutORM", back_populates="equipment_links")
    equipment = relationship("EquipmentORM", back_populates="workouts")


class MovementORM(Base):
    __tablename__ = "movements"
    __table_args__ = (UniqueConstraint("name", name="uq_movements_name"),)

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    category = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    default_load_unit = Column(String(20), nullable=True)
    video_url = Column(Text, nullable=True)

    muscles = relationship("MovementMuscleORM", back_populates="movement", cascade="all, delete-orphan")
    block_movements = relationship("WorkoutBlockMovementORM", back_populates="movement", cascade="all, delete-orphan")
    benchmarks = relationship("MovementBenchmarkORM", back_populates="movement", cascade="all, delete-orphan")
    global_performance = relationship("GlobalPerformanceDataORM", back_populates="movement", cascade="all, delete-orphan")
    skills = relationship("UserSkillORM", back_populates="movement", cascade="all, delete-orphan")
    prs = relationship("UserPROM", back_populates="movement", cascade="all, delete-orphan")


class MovementMuscleORM(Base):
    __tablename__ = "movement_muscles"
    __table_args__ = (UniqueConstraint("movement_id", "muscle_group_id", name="uq_movement_muscle"),)

    movement_id = Column(Integer, ForeignKey("movements.id", ondelete="CASCADE"), primary_key=True)
    muscle_group_id = Column(Integer, ForeignKey("muscle_groups.id"), primary_key=True)
    is_primary = Column(Boolean, nullable=False, default=True)

    movement = relationship("MovementORM", back_populates="muscles")
    muscle_group = relationship("MuscleGroupORM")


class WorkoutBlockORM(Base):
    __tablename__ = "workout_blocks"
    __table_args__ = (UniqueConstraint("workout_id", "position", name="uq_workout_block_position"),)

    id = Column(Integer, primary_key=True)
    workout_id = Column(Integer, ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False)
    position = Column(Integer, nullable=False)
    block_type = Column(String(50), nullable=True)
    title = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    rounds = Column(SmallInteger, nullable=True)
    notes = Column(Text, nullable=True)

    workout = relationship("WorkoutORM", back_populates="blocks")
    movements = relationship(
        "WorkoutBlockMovementORM", back_populates="block", cascade="all, delete-orphan", order_by="WorkoutBlockMovementORM.position"
    )


class WorkoutBlockMovementORM(Base):
    __tablename__ = "workout_block_movements"
    __table_args__ = (
        UniqueConstraint("workout_block_id", "position", name="uq_block_movement_position"),
        CheckConstraint(
            "(reps IS NOT NULL) OR (load IS NOT NULL) OR (distance_meters IS NOT NULL) OR (duration_seconds IS NOT NULL) OR (calories IS NOT NULL)",
            name="ck_block_movement_metrics_not_all_null",
        ),
    )

    id = Column(Integer, primary_key=True)
    workout_block_id = Column(Integer, ForeignKey("workout_blocks.id", ondelete="CASCADE"), nullable=False)
    movement_id = Column(Integer, ForeignKey("movements.id", ondelete="RESTRICT"), nullable=False)
    position = Column(Integer, nullable=False)
    reps = Column(Numeric(6, 2), nullable=True)
    load = Column(Numeric(6, 2), nullable=True)
    load_unit = Column(String(20), nullable=True)
    distance_meters = Column(Numeric(8, 2), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    calories = Column(Numeric(6, 2), nullable=True)

    block = relationship("WorkoutBlockORM", back_populates="movements")
    movement = relationship("MovementORM", back_populates="block_movements")


class TrainingPlanORM(Base):
    __tablename__ = "training_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    days = relationship("TrainingPlanDayORM", back_populates="plan", cascade="all, delete-orphan")


class TrainingPlanDayORM(Base):
    __tablename__ = "training_plan_days"
    __table_args__ = (UniqueConstraint("plan_id", "day_number", name="uq_plan_day"),)

    plan_id = Column(Integer, ForeignKey("training_plans.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    day_number = Column(SmallInteger, primary_key=True, nullable=False)
    focus = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)

    plan = relationship("TrainingPlanORM", back_populates="days")


class WorkoutResultORM(Base):
    __tablename__ = "workout_result"
    __table_args__ = (Index("ix_workout_result_user", "user_id"), Index("ix_workout_result_workout", "workout_id"))

    id = Column(Integer, primary_key=True, index=True)
    workout_id = Column(Integer, ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    time_seconds = Column(SmallInteger, nullable=False)
    difficulty = Column(SmallInteger, nullable=True)
    rating = Column(SmallInteger, nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())

    workout = relationship("WorkoutORM", back_populates="results")
    user = relationship("UserORM", back_populates="results")


class SimilarWorkoutORM(Base):
    __tablename__ = "similar_workouts"
    __table_args__ = (
        UniqueConstraint("workout_id", "similar_workout_id", name="uq_similar_workout"),
        CheckConstraint("workout_id <> similar_workout_id", name="ck_similar_not_same"),
        CheckConstraint("workout_id < similar_workout_id", name="ck_similar_ordering"),
    )

    workout_id = Column(Integer, ForeignKey("workouts.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    similar_workout_id = Column(Integer, ForeignKey("workouts.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    note = Column(Text, nullable=True)

    workout = relationship("WorkoutORM", foreign_keys=[workout_id], back_populates="similar_from")
    similar_workout = relationship("WorkoutORM", foreign_keys=[similar_workout_id], back_populates="similar_to")


class WorkoutStatsByLevelORM(Base):
    __tablename__ = "workout_stats_by_level"
    __table_args__ = (UniqueConstraint("workout_id", "athlete_level_id", name="uq_workout_stats_level"),)

    workout_id = Column(Integer, ForeignKey("workouts.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    athlete_level_id = Column(Integer, ForeignKey("athlete_levels.id"), primary_key=True, nullable=False)
    avg_time_seconds = Column(Numeric(8, 2), nullable=True)
    median_time_seconds = Column(Numeric(8, 2), nullable=True)
    percentile_10 = Column(Numeric(8, 2), nullable=True)
    percentile_90 = Column(Numeric(8, 2), nullable=True)
    avg_difficulty = Column(Numeric(4, 2), nullable=True)
    sample_size = Column(Integer, nullable=True)

    workout = relationship("WorkoutORM", back_populates="stats_by_level")
    athlete_level = relationship("AthleteLevelORM", back_populates="workout_stats_by_level")


class WorkoutExecutionORM(Base):
    __tablename__ = "workout_execution"
    __table_args__ = (Index("ix_workout_execution_user", "user_id"),)

    id = Column(Integer, primary_key=True)
    workout_id = Column(Integer, ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    executed_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())
    total_time_seconds = Column(Numeric(8, 2), nullable=True)
    raw_ocr_json = Column(JSONB, nullable=True)
    image_path = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    workout = relationship("WorkoutORM", back_populates="executions")
    user = relationship("UserORM", back_populates="executions")
    blocks = relationship("WorkoutExecutionBlockORM", back_populates="execution", cascade="all, delete-orphan")


class WorkoutExecutionBlockORM(Base):
    __tablename__ = "workout_execution_block"
    __table_args__ = (Index("ix_workout_execution_block_exec", "execution_id"),)

    id = Column(Integer, primary_key=True)
    execution_id = Column(Integer, ForeignKey("workout_execution.id", ondelete="CASCADE"), nullable=False)
    workout_block_id = Column(Integer, ForeignKey("workout_blocks.id", ondelete="CASCADE"), nullable=True)
    time_seconds = Column(Numeric(8, 2), nullable=True)
    hr_avg = Column(Numeric(6, 2), nullable=True)
    hr_max = Column(Numeric(6, 2), nullable=True)
    effort_score = Column(Numeric(5, 2), nullable=True)

    execution = relationship("WorkoutExecutionORM", back_populates="blocks")
    block = relationship("WorkoutBlockORM")


class WorkoutAnalysisORM(Base):
    __tablename__ = "workout_analysis"
    __table_args__ = (Index("ix_workout_analysis_user", "user_id"),)

    id = Column(Integer, primary_key=True)
    workout_id = Column(Integer, ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    analysis_json = Column(JSONB, nullable=True)
    athlete_impact = Column(JSONB, nullable=True)
    applied = Column(Boolean, nullable=False, server_default=func.false(), default=False)
    applied_at = Column(DateTime(timezone=False), nullable=True)
    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())

    workout = relationship("WorkoutORM")
    user = relationship("UserORM")


class GlobalPerformanceDataORM(Base):
    __tablename__ = "global_performance_data"
    __table_args__ = (Index("ix_global_perf_level", "athlete_level_id"),)

    id = Column(Integer, primary_key=True)
    workout_id = Column(Integer, ForeignKey("workouts.id", ondelete="CASCADE"), nullable=True)
    movement_id = Column(Integer, ForeignKey("movements.id", ondelete="CASCADE"), nullable=True)
    athlete_level_id = Column(Integer, ForeignKey("athlete_levels.id"), nullable=True)
    source = Column(String(50), nullable=True)
    avg_time_seconds = Column(Numeric(8, 2), nullable=True)
    avg_reps = Column(Numeric(8, 2), nullable=True)
    avg_load = Column(Numeric(8, 2), nullable=True)
    percentile_25 = Column(Numeric(8, 2), nullable=True)
    percentile_50 = Column(Numeric(8, 2), nullable=True)
    percentile_75 = Column(Numeric(8, 2), nullable=True)
    percentile_90 = Column(Numeric(8, 2), nullable=True)
    updated_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())

    movement = relationship("MovementORM", back_populates="global_performance")
    athlete_level = relationship("AthleteLevelORM")
    workout = relationship("WorkoutORM", back_populates="global_performance")


class MovementBenchmarkORM(Base):
    __tablename__ = "movement_benchmarks"
    __table_args__ = (UniqueConstraint("movement_id", "athlete_level_id", name="uq_movement_benchmark"),)

    id = Column(Integer, primary_key=True)
    movement_id = Column(Integer, ForeignKey("movements.id", ondelete="CASCADE"), nullable=False)
    athlete_level_id = Column(Integer, ForeignKey("athlete_levels.id"), nullable=False)
    avg_score = Column(Numeric(8, 2), nullable=True)
    percentile_25 = Column(Numeric(8, 2), nullable=True)
    percentile_50 = Column(Numeric(8, 2), nullable=True)
    percentile_75 = Column(Numeric(8, 2), nullable=True)
    percentile_90 = Column(Numeric(8, 2), nullable=True)
    unit = Column(String(20), nullable=True)
    updated_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())

    movement = relationship("MovementORM", back_populates="benchmarks")
    athlete_level = relationship("AthleteLevelORM", back_populates="movement_benchmarks")


class GlobalCapacityBenchmarkORM(Base):
    __tablename__ = "global_capacity_benchmarks"
    __table_args__ = (UniqueConstraint("capacity_id", "athlete_level_id", name="uq_global_capacity_bench"),)

    id = Column(Integer, primary_key=True)
    capacity_id = Column(Integer, ForeignKey("physical_capacities.id", ondelete="CASCADE"), nullable=False)
    athlete_level_id = Column(Integer, ForeignKey("athlete_levels.id"), nullable=False)
    avg_value = Column(Numeric(8, 2), nullable=True)
    percentile_50 = Column(Numeric(8, 2), nullable=True)
    percentile_90 = Column(Numeric(8, 2), nullable=True)
    updated_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())

    capacity = relationship("PhysicalCapacityORM")
    athlete_level = relationship("AthleteLevelORM", back_populates="capacity_benchmarks")


class AchievementORM(Base):
    __tablename__ = "achievements"
    __table_args__ = (UniqueConstraint("code", name="uq_achievements_code"),)

    id = Column(Integer, primary_key=True)
    code = Column(String(100), nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)
    xp_reward = Column(Numeric(10, 2), nullable=False, server_default="0")
    icon_url = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default=func.true())

    user_achievements = relationship("UserAchievementORM", back_populates="achievement", cascade="all, delete-orphan")


class UserAchievementORM(Base):
    __tablename__ = "user_achievements"
    __table_args__ = (
        UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),
        Index("ix_user_achievements_user", "user_id"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False)
    unlocked_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())

    user = relationship("UserORM", back_populates="achievements")
    achievement = relationship("AchievementORM", back_populates="user_achievements")


class MissionORM(Base):
    __tablename__ = "missions"

    id = Column(Integer, primary_key=True)
    type = Column(String(20), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    xp_reward = Column(Numeric(10, 2), nullable=False, server_default="0")
    condition_json = Column(JSONB, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default=func.true())

    user_missions = relationship("UserMissionORM", back_populates="mission", cascade="all, delete-orphan")


class UserMissionORM(Base):
    __tablename__ = "user_missions"
    __table_args__ = (
        UniqueConstraint("user_id", "mission_id", name="uq_user_mission"),
        Index("ix_user_missions_user", "user_id"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    mission_id = Column(Integer, ForeignKey("missions.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), nullable=False, server_default="assigned")
    progress_value = Column(Numeric(8, 2), nullable=False, server_default="0")
    assigned_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=False), nullable=True)
    expires_at = Column(DateTime(timezone=False), nullable=True)

    user = relationship("UserORM", back_populates="missions")
    mission = relationship("MissionORM", back_populates="user_missions")
