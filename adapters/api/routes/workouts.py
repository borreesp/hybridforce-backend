import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from application.schemas.workouts import (
    WorkoutCreate,
    WorkoutUpdate,
    WorkoutRead,
    WorkoutFilter,
    WorkoutLevelTimeSchema,
    WorkoutCapacitySchema,
    WorkoutHyroxStationSchema,
    WorkoutAnalysisResponse,
)
from application.services import WorkoutService
from domain.models.enums import AthleteLevel, EnergyDomain, MuscleGroup
from infrastructure.db.session import get_session
from infrastructure.db.models import WorkoutORM

router = APIRouter()
analysis_router = APIRouter()


def _decimal_to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def to_read_model(workout: WorkoutORM) -> WorkoutRead:
    meta = workout.metadata_rel
    stats = workout.stats
    return WorkoutRead(
        id=workout.id,
        parent_workout_id=workout.parent_workout_id,
        version=workout.version,
        is_active=workout.is_active,
        title=workout.title,
        description=workout.description,
        domain=workout.domain.code if workout.domain else None,
        intensity=workout.intensity_level.code if workout.intensity_level else None,
        hyrox_transfer=workout.hyrox_transfer_level.code if workout.hyrox_transfer_level else None,
        wod_type=workout.wod_type,
        volume_total=meta.volume_total if meta else None,
        work_rest_ratio=meta.work_rest_ratio if meta else None,
        dominant_stimulus=meta.dominant_stimulus if meta else None,
        load_type=meta.load_type if meta else None,
        estimated_difficulty=_decimal_to_float(stats.estimated_difficulty) if stats else None,
        main_muscle_chain=workout.main_muscle_group.code if workout.main_muscle_group else None,
        athlete_profile_desc=meta.athlete_profile_desc if meta else None,
        target_athlete_desc=meta.target_athlete_desc if meta else None,
        session_load=meta.session_load if meta else None,
        session_feel=meta.session_feel if meta else None,
        official_tag=workout.official_tag,
        pacing_tip=meta.pacing_tip if meta else None,
        pacing_detail=meta.pacing_detail if meta else None,
        break_tip=meta.break_tip if meta else None,
        rx_variant=meta.rx_variant if meta else None,
        scaled_variant=meta.scaled_variant if meta else None,
        ai_observation=meta.ai_observation if meta else None,
        avg_time_seconds=stats.avg_time_seconds if stats else None,
        avg_rating=_decimal_to_float(stats.avg_rating) if stats and stats.avg_rating is not None else None,
        avg_difficulty=_decimal_to_float(stats.avg_difficulty) if stats and stats.avg_difficulty is not None else None,
        rating_count=stats.rating_count if stats else None,
        level_times=[
            WorkoutLevelTimeSchema(
                athlete_level=lt.athlete_level.code if lt.athlete_level else None,
                time_minutes=_decimal_to_float(lt.time_minutes),
                time_range=lt.time_range,
            )
            for lt in workout.level_times
        ],
        capacities=[
            WorkoutCapacitySchema(capacity=cap.capacity.code if cap.capacity else None, value=cap.value, note=cap.note)
            for cap in workout.capacities
        ],
        hyrox_stations=[
            WorkoutHyroxStationSchema(station=hs.station.code if hs.station else None, transfer_pct=hs.transfer_pct)
            for hs in workout.hyrox_stations
        ],
        muscles=[m.muscle_group.code if m.muscle_group else None for m in workout.muscles],
        equipment_ids=[eq.equipment_id for eq in workout.equipment_links],
        similar_workout_ids=[sim.similar_workout_id for sim in workout.similar_from],
    )


@router.get("/", response_model=List[WorkoutRead])
def list_workouts(
    level: Optional[AthleteLevel] = Query(None),
    domain: Optional[EnergyDomain] = Query(None),
    muscle: Optional[MuscleGroup] = Query(None),
    session: Session = Depends(get_session),
):
    service = WorkoutService(session)
    filters = WorkoutFilter(level=level, domain=domain, muscle=muscle)
    workouts = service.list(filters)
    return [to_read_model(workout) for workout in workouts]


@router.post("/", response_model=WorkoutRead, status_code=status.HTTP_201_CREATED)
def create_workout(payload: WorkoutCreate, session: Session = Depends(get_session)):
    service = WorkoutService(session)
    workout = service.create(payload)
    return to_read_model(workout)


@router.get("/{workout_id}", response_model=WorkoutRead)
def get_workout(workout_id: int, session: Session = Depends(get_session)):
    service = WorkoutService(session)
    workout = service.get(workout_id)
    if not workout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")
    return to_read_model(workout)


@router.put("/{workout_id}", response_model=WorkoutRead)
def update_workout(workout_id: int, payload: WorkoutUpdate, session: Session = Depends(get_session)):
    service = WorkoutService(session)
    updated = service.update(workout_id, payload)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")
    return to_read_model(updated)


@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout(workout_id: int, session: Session = Depends(get_session)):
    service = WorkoutService(session)
    deleted = service.delete(workout_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")
    return None


@router.get("/{workout_id}/analysis", response_model=WorkoutAnalysisResponse)
def workout_analysis(workout_id: int, session: Session = Depends(get_session)):
    service = WorkoutService(session)
    analysis = service.analysis(workout_id)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")
    return analysis


@analysis_router.post("/workout-analysis", response_model=WorkoutAnalysisResponse)
async def analyze_workout_payload(
    payload: Optional[WorkoutCreate] = None,
    file: Optional[UploadFile] = None,
    session: Session = Depends(get_session),
):
    service = WorkoutService(session)
    data = payload
    if file:
        content = await file.read()
        try:
            parsed = json.loads(content.decode())
            data = WorkoutCreate.model_validate(parsed)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid file payload: {exc}") from exc
    if data is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing workout data")
    return service.analyze_payload(data.model_dump())


@router.get("/{workout_id}/similar", response_model=List[WorkoutRead])
def similar_workouts(workout_id: int, session: Session = Depends(get_session)):
    service = WorkoutService(session)
    workouts = service.similar(workout_id)
    return [to_read_model(workout) for workout in workouts]
