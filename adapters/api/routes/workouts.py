import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status, Request
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
    WorkoutStatsRead,
)
from application.schemas.workout_blocks import WorkoutBlockSchema, WorkoutBlockMovementSchema
from application.schemas.movements import MovementRead, MovementMuscleSchema
from application.services import WorkoutService
from application.services.xp_service import compute_xp_estimate
from domain.services.workout_analysis import analyze_workout
from domain.models.enums import EnergyDomain, MuscleGroup
from infrastructure.db.session import get_session
from infrastructure.auth.dependencies import get_current_user
from infrastructure.db.models import WorkoutORM, UserORM

router = APIRouter()
analysis_router = APIRouter(dependencies=[Depends(get_current_user)])


def _decimal_to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def _movement_to_read(movement) -> MovementRead:
    return MovementRead(
        id=movement.id,
        name=movement.name,
        category=movement.category,
        description=movement.description,
        default_load_unit=movement.default_load_unit,
        video_url=movement.video_url,
        muscles=[
            MovementMuscleSchema(muscle_group=mm.muscle_group.code if mm.muscle_group else "", is_primary=mm.is_primary)
            for mm in movement.muscles
        ],
    )


def _block_to_schema(block) -> WorkoutBlockSchema:
    return WorkoutBlockSchema(
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
            WorkoutBlockMovementSchema(
                id=mv.id,
                movement_id=mv.movement_id,
                position=mv.position,
                reps=_decimal_to_float(mv.reps),
                load=_decimal_to_float(mv.load),
                load_unit=mv.load_unit,
                distance_meters=_decimal_to_float(mv.distance_meters),
                duration_seconds=mv.duration_seconds,
                calories=_decimal_to_float(mv.calories),
                movement=_movement_to_read(mv.movement) if mv.movement else None,
            )
            for mv in block.movements
        ],
    )


def _compute_xp_estimate_from_workout(service: WorkoutService, workout: WorkoutORM) -> Optional[int]:
    try:
        domain_model = service._to_domain(workout)
        analysis = analyze_workout(domain_model)
        fatigue = analysis.get("fatigue_score")
        if fatigue is None:
            return None
        return int(compute_xp_estimate(float(fatigue), None)["xp"])
    except Exception:
        return None


def to_read_model(workout: WorkoutORM, include_structure: bool = False, xp_estimate: Optional[int] = None) -> WorkoutRead:
    meta = workout.metadata_rel
    stats = workout.stats
    return WorkoutRead(
        id=workout.id,
        xp_estimate=xp_estimate,
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
        extra_attributes_json=meta.extra_attributes_json if meta else None,
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
        blocks=[_block_to_schema(block) for block in workout.blocks] if include_structure else [],
    )


@router.get("/", response_model=List[WorkoutRead])
def list_workouts(
    level: Optional[str] = Query(None),
    domain: Optional[EnergyDomain] = Query(None),
    muscle: Optional[MuscleGroup] = Query(None),
    session: Session = Depends(get_session),
):
    service = WorkoutService(session)
    filters = WorkoutFilter(level=level, domain=domain, muscle=muscle)
    workouts = service.list(filters)
    result: List[WorkoutRead] = []
    for workout in workouts:
        xp_estimate = _compute_xp_estimate_from_workout(service, workout)
        result.append(to_read_model(workout, xp_estimate=xp_estimate))
    return result


@router.get("/stats", response_model=List[WorkoutStatsRead])
def list_workout_stats(session: Session = Depends(get_session)):
    service = WorkoutService(session)
    workouts = service.stats()
    return [
        WorkoutStatsRead(
            workout_id=w.id,
            title=w.title,
            estimated_difficulty=_decimal_to_float(w.stats.estimated_difficulty) if w.stats else None,
            avg_time_seconds=w.stats.avg_time_seconds if w.stats else None,
            avg_rating=_decimal_to_float(w.stats.avg_rating) if w.stats else None,
            avg_difficulty=_decimal_to_float(w.stats.avg_difficulty) if w.stats else None,
            rating_count=w.stats.rating_count if w.stats else None,
        )
        for w in workouts
        if w.stats
    ]


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
    xp_estimate = _compute_xp_estimate_from_workout(service, workout)
    return to_read_model(workout, xp_estimate=xp_estimate)


@router.get("/{workout_id}/structure", response_model=WorkoutRead)
def get_workout_structure(workout_id: int, session: Session = Depends(get_session)):
    service = WorkoutService(session)
    workout = service.structure(workout_id)
    if not workout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")
    xp_estimate = _compute_xp_estimate_from_workout(service, workout)
    return to_read_model(workout, include_structure=True, xp_estimate=xp_estimate)


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


def _level_from_user(user: UserORM | None) -> int | None:
    if not user:
        return None
    level_code = getattr(getattr(user, "athlete_level", None), "code", None)
    if isinstance(level_code, str) and level_code.upper().startswith("L"):
        try:
            return int("".join(ch for ch in level_code if ch.isdigit()))
        except ValueError:
            pass
    # fallback: try athlete_level_id or id numeric
    level_id = getattr(user, "athlete_level_id", None)
    if isinstance(level_id, int):
        return level_id
    return None


def _with_xp_estimate(analysis: dict, user: Optional[UserORM]) -> dict:
    fatigue = analysis.get("fatigue_score")
    if fatigue is None:
        return analysis
    level = _level_from_user(user)
    xp_data = compute_xp_estimate(float(fatigue), level)
    analysis["xp_estimate"] = int(xp_data["xp"])
    analysis["xp_components"] = xp_data
    return analysis


def get_current_user_optional(request: Request, session: Session = Depends(get_session)) -> Optional[UserORM]:
    try:
        return get_current_user(request=request, session=session)
    except Exception:
        return None


@router.get("/{workout_id}/analysis", response_model=WorkoutAnalysisResponse)
def workout_analysis(
    workout_id: int,
    session: Session = Depends(get_session),
    current_user: Optional[UserORM] = Depends(get_current_user_optional),
):
    service = WorkoutService(session)
    analysis = service.analysis(workout_id)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")
    return _with_xp_estimate(analysis, current_user)


@analysis_router.post("/workout-analysis", response_model=WorkoutAnalysisResponse)
async def analyze_workout_payload(
    payload: Optional[WorkoutCreate] = None,
    file: Optional[UploadFile] = None,
    session: Session = Depends(get_session),
    current_user: Optional[UserORM] = Depends(get_current_user_optional),
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
    analysis = service.analyze_payload(data.model_dump())
    return _with_xp_estimate(analysis, current_user)


@router.get("/{workout_id}/similar", response_model=List[WorkoutRead])
def similar_workouts(workout_id: int, session: Session = Depends(get_session)):
    service = WorkoutService(session)
    workouts = service.similar(workout_id)
    return [to_read_model(workout) for workout in workouts]


@router.get("/{workout_id}/blocks", response_model=List[WorkoutBlockSchema])
def workout_blocks(workout_id: int, session: Session = Depends(get_session)):
    service = WorkoutService(session)
    workout = service.structure(workout_id)
    if not workout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")
    return [WorkoutBlockSchema.model_validate(block) for block in workout.blocks]


@router.get("/{workout_id}/versions", response_model=List[WorkoutRead])
def workout_versions(workout_id: int, session: Session = Depends(get_session)):
    service = WorkoutService(session)
    versions = service.versions(workout_id)
    if not versions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")
    return [to_read_model(w) for w in versions]
