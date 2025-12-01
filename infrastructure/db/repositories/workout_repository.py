from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from domain.models.enums import AthleteLevel, EnergyDomain, IntensityLevel, MuscleGroup
from infrastructure.db.models import (
    AthleteLevelORM,
    EnergyDomainORM,
    EquipmentORM,
    HyroxStationORM,
    IntensityLevelORM,
    MuscleGroupORM,
    PhysicalCapacityORM,
    SimilarWorkoutORM,
    MovementMuscleORM,
    MovementORM,
    WorkoutBlockMovementORM,
    WorkoutBlockORM,
    WorkoutCapacityORM,
    WorkoutEquipmentORM,
    WorkoutHyroxStationORM,
    WorkoutLevelTimeORM,
    WorkoutMetadataORM,
    WorkoutMuscleORM,
    WorkoutORM,
    WorkoutStatsORM,
)
from .base import BaseRepository


def _lookup_id(session: Session, model, code):
    if code is None:
        return None
    code_value = getattr(code, "value", code)
    row = session.query(model).filter(model.code == code_value).first()
    return row.id if row else None


class WorkoutRepository(BaseRepository):
    def __init__(self, session: Session):
        super().__init__(session, WorkoutORM)

    def list_filtered(
        self, level: Optional[AthleteLevel] = None, domain: Optional[EnergyDomain] = None, muscle: Optional[MuscleGroup] = None
    ):
        query = self.session.query(WorkoutORM).options(
            joinedload(WorkoutORM.metadata_rel),
            joinedload(WorkoutORM.stats),
        )
        if domain:
            domain_id = _lookup_id(self.session, EnergyDomainORM, domain.value)
            if domain_id:
                query = query.filter(WorkoutORM.domain_id == domain_id)
        if level:
            level_id = _lookup_id(self.session, AthleteLevelORM, level.value)
            if level_id:
                query = query.join(WorkoutLevelTimeORM).filter(WorkoutLevelTimeORM.athlete_level_id == level_id)
        if muscle:
            muscle_id = _lookup_id(self.session, MuscleGroupORM, muscle.value)
            if muscle_id:
                query = query.join(WorkoutMuscleORM).filter(WorkoutMuscleORM.muscle_group_id == muscle_id)
        return query.distinct().all()

    def create_with_relations(self, payload: dict):
        level_times = payload.pop("level_times", [])
        capacities = payload.pop("capacities", [])
        hyrox_stations = payload.pop("hyrox_stations", [])
        muscles = payload.pop("muscles", [])
        equipment_ids = payload.pop("equipment_ids", [])
        similar_ids = payload.pop("similar_workout_ids", [])

        metadata_fields = {
            "volume_total",
            "work_rest_ratio",
            "dominant_stimulus",
            "load_type",
            "athlete_profile_desc",
            "target_athlete_desc",
            "pacing_tip",
            "pacing_detail",
            "break_tip",
            "rx_variant",
            "scaled_variant",
            "ai_observation",
            "session_load",
            "session_feel",
            "extra_attributes_json",
        }
        stats_fields = {"estimated_difficulty", "avg_time_seconds", "avg_rating", "avg_difficulty", "rating_count"}

        metadata_payload = {k: payload.pop(k) for k in list(payload.keys()) if k in metadata_fields}
        stats_payload = {k: payload.pop(k) for k in list(payload.keys()) if k in stats_fields}

        self._attach_lookup_ids(payload)

        workout = WorkoutORM(**payload)
        self.session.add(workout)
        self.session.flush()

        workout.metadata_rel = WorkoutMetadataORM(workout_id=workout.id, **metadata_payload)
        workout.stats = WorkoutStatsORM(workout_id=workout.id, **stats_payload)

        self._apply_children(workout, level_times, capacities, hyrox_stations, muscles, equipment_ids, similar_ids)
        self.session.commit()
        self.session.refresh(workout)
        return workout

    def update_with_relations(self, workout: WorkoutORM, payload: dict):
        level_times = payload.pop("level_times", None)
        capacities = payload.pop("capacities", None)
        hyrox_stations = payload.pop("hyrox_stations", None)
        muscles = payload.pop("muscles", None)
        equipment_ids = payload.pop("equipment_ids", None)
        similar_ids = payload.pop("similar_workout_ids", None)

        metadata_fields = {
            "volume_total",
            "work_rest_ratio",
            "dominant_stimulus",
            "load_type",
            "athlete_profile_desc",
            "target_athlete_desc",
            "pacing_tip",
            "pacing_detail",
            "break_tip",
            "rx_variant",
            "scaled_variant",
            "ai_observation",
            "session_load",
            "session_feel",
            "extra_attributes_json",
        }
        stats_fields = {"estimated_difficulty", "avg_time_seconds", "avg_rating", "avg_difficulty", "rating_count"}

        metadata_payload = {k: payload.pop(k) for k in list(payload.keys()) if k in metadata_fields}
        stats_payload = {k: payload.pop(k) for k in list(payload.keys()) if k in stats_fields}

        self._attach_lookup_ids(payload)

        for key, value in payload.items():
            setattr(workout, key, value)

        if metadata_payload:
            if not workout.metadata_rel:
                workout.metadata_rel = WorkoutMetadataORM(workout_id=workout.id, **metadata_payload)
            else:
                for key, value in metadata_payload.items():
                    setattr(workout.metadata_rel, key, value)
        if stats_payload:
            if not workout.stats:
                workout.stats = WorkoutStatsORM(workout_id=workout.id, **stats_payload)
            else:
                for key, value in stats_payload.items():
                    setattr(workout.stats, key, value)

        if level_times is not None:
            workout.level_times.clear()
        if capacities is not None:
            workout.capacities.clear()
        if hyrox_stations is not None:
            workout.hyrox_stations.clear()
        if muscles is not None:
            workout.muscles.clear()
        if equipment_ids is not None:
            workout.equipment_links.clear()
        if similar_ids is not None:
            workout.similar_from.clear()

        self._apply_children(
            workout,
            level_times or [],
            capacities or [],
            hyrox_stations or [],
            muscles or [],
            equipment_ids or [],
            similar_ids or [],
        )
        self.session.commit()
        self.session.refresh(workout)
        return workout

    def _attach_lookup_ids(self, payload: dict):
        if "domain" in payload:
            payload["domain_id"] = _lookup_id(self.session, EnergyDomainORM, payload.pop("domain"))
        if "intensity" in payload:
            payload["intensity_level_id"] = _lookup_id(self.session, IntensityLevelORM, payload.pop("intensity"))
        if "hyrox_transfer" in payload:
            payload["hyrox_transfer_level_id"] = _lookup_id(self.session, IntensityLevelORM, payload.pop("hyrox_transfer"))
        if "main_muscle_chain" in payload:
            payload["main_muscle_group_id"] = _lookup_id(self.session, MuscleGroupORM, payload.pop("main_muscle_chain"))

    def _apply_children(
        self,
        workout: WorkoutORM,
        level_times: list,
        capacities: list,
        hyrox_stations: list,
        muscles: list,
        equipment_ids: list[int],
        similar_ids: list[int],
    ):
        for lt in level_times:
            level_id = _lookup_id(self.session, AthleteLevelORM, lt["athlete_level"])
            if level_id:
                workout.level_times.append(
                    WorkoutLevelTimeORM(
                        workout_id=workout.id,
                        athlete_level_id=level_id,
                        time_minutes=lt["time_minutes"],
                        time_range=lt["time_range"],
                    )
                )
        for cap in capacities:
            cap_id = _lookup_id(self.session, PhysicalCapacityORM, cap["capacity"])
            if cap_id:
                workout.capacities.append(
                    WorkoutCapacityORM(
                        workout_id=workout.id,
                        capacity_id=cap_id,
                        value=cap["value"],
                        note=cap["note"],
                    )
                )
        for hyrox in hyrox_stations:
            station_id = _lookup_id(self.session, HyroxStationORM, hyrox["station"])
            if station_id:
                workout.hyrox_stations.append(
                    WorkoutHyroxStationORM(
                        workout_id=workout.id,
                        station_id=station_id,
                        transfer_pct=hyrox["transfer_pct"],
                    )
                )
        for muscle in muscles:
            muscle_id = _lookup_id(self.session, MuscleGroupORM, muscle)
            if muscle_id:
                workout.muscles.append(WorkoutMuscleORM(workout_id=workout.id, muscle_group_id=muscle_id))
        if equipment_ids:
            equipments = self.session.query(EquipmentORM).filter(EquipmentORM.id.in_(equipment_ids)).all()
            for eq in equipments:
                workout.equipment_links.append(WorkoutEquipmentORM(workout_id=workout.id, equipment_id=eq.id))
        if similar_ids:
            for sid in similar_ids:
                workout.similar_from.append(SimilarWorkoutORM(workout_id=workout.id, similar_workout_id=sid))

    def get_similar_workouts(self, workout_id: int) -> List[WorkoutORM]:
        similar_rel = self.session.query(SimilarWorkoutORM).filter(SimilarWorkoutORM.workout_id == workout_id).all()
        ids = [rel.similar_workout_id for rel in similar_rel]
        if not ids:
            return []
        return self.session.query(WorkoutORM).filter(WorkoutORM.id.in_(ids)).all()

    def get_with_structure(self, workout_id: int) -> WorkoutORM | None:
        return (
            self.session.query(WorkoutORM)
            .options(
                joinedload(WorkoutORM.metadata_rel),
                joinedload(WorkoutORM.stats),
                joinedload(WorkoutORM.level_times).joinedload(WorkoutLevelTimeORM.athlete_level),
                joinedload(WorkoutORM.capacities).joinedload(WorkoutCapacityORM.capacity),
                joinedload(WorkoutORM.hyrox_stations).joinedload(WorkoutHyroxStationORM.station),
                joinedload(WorkoutORM.muscles).joinedload(WorkoutMuscleORM.muscle_group),
                joinedload(WorkoutORM.blocks)
                .joinedload(WorkoutBlockORM.movements)
                .joinedload(WorkoutBlockMovementORM.movement)
                .joinedload(MovementORM.muscles)
                .joinedload(MovementMuscleORM.muscle_group),
            )
            .filter(WorkoutORM.id == workout_id)
            .first()
        )

    def list_versions(self, workout_id: int) -> List[WorkoutORM]:
        workout = self.get(workout_id)
        if not workout:
            return []
        root_id = workout.parent_workout_id or workout.id
        return (
            self.session.query(WorkoutORM)
            .options(joinedload(WorkoutORM.metadata_rel), joinedload(WorkoutORM.stats))
            .filter(or_(WorkoutORM.id == root_id, WorkoutORM.parent_workout_id == root_id))
            .order_by(WorkoutORM.version.asc())
            .all()
        )

    def list_stats(self) -> List[WorkoutORM]:
        return self.session.query(WorkoutORM).options(joinedload(WorkoutORM.stats)).all()
