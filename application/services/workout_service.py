from decimal import Decimal
from typing import Optional

from application.schemas.workouts import WorkoutCreate, WorkoutUpdate, WorkoutFilter
from domain.models.entities import (
    Workout,
    WorkoutLevelTime,
    WorkoutCapacity,
    WorkoutHyroxStation,
    WorkoutMuscle,
    WorkoutEquipment,
    WorkoutBlock,
    WorkoutBlockMovement,
    Movement,
    MovementMuscle,
)
from domain.models.enums import EnergyDomain, IntensityLevel, MuscleGroup, PhysicalCapacity, AthleteLevel, HyroxStation
from domain.services.workout_analysis import analyze_workout
from infrastructure.db.models import WorkoutORM
from infrastructure.db.repositories import WorkoutRepository


def _to_float(value):
    return float(value) if isinstance(value, Decimal) else value


class WorkoutService:
    def __init__(self, session):
        self.repo = WorkoutRepository(session)

    def list(self, filters: WorkoutFilter):
        return self.repo.list_filtered(filters.level, filters.domain, filters.muscle)

    def get(self, workout_id: int) -> Optional[WorkoutORM]:
        return self.repo.get(workout_id)

    def create(self, data: WorkoutCreate):
        payload = data.model_dump()
        return self.repo.create_with_relations(payload)

    def update(self, workout_id: int, data: WorkoutUpdate):
        workout = self.repo.get(workout_id)
        if not workout:
            return None
        payload = data.model_dump(exclude_none=True)
        return self.repo.update_with_relations(workout, payload)

    def delete(self, workout_id: int):
        workout = self.repo.get(workout_id)
        if not workout:
            return None
        return self.repo.delete(workout)

    def similar(self, workout_id: int):
        return self.repo.get_similar_workouts(workout_id)

    def analysis(self, workout_id: int):
        workout = self.repo.get(workout_id)
        if not workout:
            return None
        domain_model = self._to_domain(workout)
        return analyze_workout(domain_model)

    def analyze_payload(self, payload: dict):
        workout_input = WorkoutCreate.model_validate(payload)
        domain_model = self._to_domain_from_payload(workout_input)
        return analyze_workout(domain_model)

    def structure(self, workout_id: int):
        return self.repo.get_with_structure(workout_id)

    def versions(self, workout_id: int):
        return self.repo.list_versions(workout_id)

    def stats(self):
        return self.repo.list_stats()

    def _to_domain(self, workout: WorkoutORM) -> Workout:
        metadata = workout.metadata_rel
        stats = workout.stats
        domain_code = workout.domain.code if workout.domain else None
        intensity_code = workout.intensity_level.code if workout.intensity_level else None
        hyrox_code = workout.hyrox_transfer_level.code if workout.hyrox_transfer_level else None
        main_muscle_code = workout.main_muscle_group.code if workout.main_muscle_group else None
        return Workout(
            id=workout.id,
            parent_workout_id=workout.parent_workout_id,
            version=workout.version,
            is_active=workout.is_active,
            title=workout.title,
            description=workout.description,
            domain=EnergyDomain(domain_code) if domain_code else None,
            intensity=IntensityLevel(intensity_code) if intensity_code else None,
            hyrox_transfer=IntensityLevel(hyrox_code) if hyrox_code else None,
            wod_type=workout.wod_type,
            volume_total=metadata.volume_total if metadata else None,
            work_rest_ratio=metadata.work_rest_ratio if metadata else None,
            dominant_stimulus=metadata.dominant_stimulus if metadata else None,
            load_type=metadata.load_type if metadata else None,
            estimated_difficulty=_to_float(stats.estimated_difficulty) if stats else None,
            main_muscle_chain=MuscleGroup(main_muscle_code) if main_muscle_code else None,
            extra_attributes_json=metadata.extra_attributes_json if metadata else None,
            athlete_profile_desc=metadata.athlete_profile_desc if metadata else None,
            target_athlete_desc=metadata.target_athlete_desc if metadata else None,
            session_load=metadata.session_load if metadata else None,
            session_feel=metadata.session_feel if metadata else None,
            official_tag=workout.official_tag,
            pacing_tip=metadata.pacing_tip if metadata else None,
            pacing_detail=metadata.pacing_detail if metadata else None,
            break_tip=metadata.break_tip if metadata else None,
            rx_variant=metadata.rx_variant if metadata else None,
            scaled_variant=metadata.scaled_variant if metadata else None,
            ai_observation=metadata.ai_observation if metadata else None,
            avg_time_seconds=stats.avg_time_seconds if stats else None,
            avg_rating=_to_float(stats.avg_rating) if stats and stats.avg_rating is not None else None,
            avg_difficulty=_to_float(stats.avg_difficulty) if stats and stats.avg_difficulty is not None else None,
            rating_count=stats.rating_count if stats else None,
            level_times=[
                WorkoutLevelTime(
                    workout_id=lt.workout_id,
                    athlete_level=AthleteLevel(lt.athlete_level.code) if lt.athlete_level else None,
                    time_minutes=_to_float(lt.time_minutes),
                    time_range=lt.time_range,
                )
                for lt in workout.level_times
            ],
            capacities=[
                WorkoutCapacity(
                    workout_id=cap.workout_id,
                    capacity=PhysicalCapacity(cap.capacity.code) if cap.capacity else None,
                    value=cap.value,
                    note=cap.note,
                )
                for cap in workout.capacities
            ],
            hyrox_stations=[
                WorkoutHyroxStation(
                    workout_id=hs.workout_id,
                    station=HyroxStation(hs.station.code) if hs.station else None,
                    transfer_pct=hs.transfer_pct,
                )
                for hs in workout.hyrox_stations
            ],
            muscles=[
                WorkoutMuscle(workout_id=m.workout_id, muscle=MuscleGroup(m.muscle_group.code) if m.muscle_group else None)
                for m in workout.muscles
            ],
            equipment=[WorkoutEquipment(workout_id=eq.workout_id, equipment_id=eq.equipment_id) for eq in workout.equipment_links],
            blocks=[
                WorkoutBlock(
                    id=block.id,
                    workout_id=block.workout_id,
                    position=block.position,
                    block_type=block.block_type,
                    title=block.title,
                    description=block.description,
                    duration_seconds=block.duration_seconds,
                    rounds=block.rounds,
                    notes=block.notes,
                    movements=[
                        WorkoutBlockMovement(
                            id=mv.id,
                            movement_id=mv.movement_id,
                            position=mv.position,
                            reps=_to_float(mv.reps),
                            load=_to_float(mv.load),
                            load_unit=mv.load_unit,
                            distance_meters=_to_float(mv.distance_meters),
                            duration_seconds=mv.duration_seconds,
                            calories=_to_float(mv.calories),
                            movement=Movement(
                                id=mv.movement.id if mv.movement else None,
                                name=mv.movement.name if mv.movement else "",
                                category=mv.movement.category if mv.movement else None,
                                description=mv.movement.description if mv.movement else None,
                                default_load_unit=mv.movement.default_load_unit if mv.movement else None,
                                video_url=mv.movement.video_url if mv.movement else None,
                                muscles=[
                                    MovementMuscle(
                                        movement_id=muscle.movement_id,
                                        muscle_group=MuscleGroup(muscle.muscle_group.code),
                                        is_primary=muscle.is_primary,
                                    )
                                    for muscle in (mv.movement.muscles if mv.movement else [])
                                    if muscle.muscle_group
                                ],
                            ),
                        )
                        for mv in block.movements
                    ],
                )
                for block in workout.blocks
            ],
        )

    def _to_domain_from_payload(self, data: WorkoutCreate) -> Workout:
        return Workout(
            parent_workout_id=data.parent_workout_id,
            version=data.version,
            is_active=data.is_active,
            title=data.title,
            description=data.description,
            domain=data.domain,
            intensity=data.intensity,
            hyrox_transfer=data.hyrox_transfer,
            wod_type=data.wod_type,
            volume_total=data.volume_total,
            work_rest_ratio=data.work_rest_ratio,
            dominant_stimulus=data.dominant_stimulus,
            load_type=data.load_type,
            estimated_difficulty=data.estimated_difficulty,
            main_muscle_chain=data.main_muscle_chain,
            extra_attributes_json=data.extra_attributes_json,
            athlete_profile_desc=data.athlete_profile_desc,
            target_athlete_desc=data.target_athlete_desc,
            session_load=data.session_load,
            session_feel=data.session_feel,
            official_tag=data.official_tag,
            pacing_tip=data.pacing_tip,
            pacing_detail=data.pacing_detail,
            break_tip=data.break_tip,
            rx_variant=data.rx_variant,
            scaled_variant=data.scaled_variant,
            ai_observation=data.ai_observation,
            avg_time_seconds=data.avg_time_seconds,
            avg_rating=data.avg_rating,
            avg_difficulty=data.avg_difficulty,
            rating_count=data.rating_count,
            level_times=[
                WorkoutLevelTime(
                    workout_id=0,
                    athlete_level=lt.athlete_level,
                    time_minutes=lt.time_minutes,
                    time_range=lt.time_range,
                )
                for lt in data.level_times
            ],
            capacities=[
                WorkoutCapacity(workout_id=0, capacity=cap.capacity, value=cap.value, note=cap.note)
                for cap in data.capacities
            ],
            hyrox_stations=[
                WorkoutHyroxStation(workout_id=0, station=hs.station, transfer_pct=hs.transfer_pct) for hs in data.hyrox_stations
            ],
            muscles=[WorkoutMuscle(workout_id=0, muscle=m) for m in data.muscles],
            equipment=[WorkoutEquipment(workout_id=0, equipment_id=eq) for eq in data.equipment_ids],
        )
