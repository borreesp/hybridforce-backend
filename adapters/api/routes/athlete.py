import logging
from datetime import datetime, date
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from application.schemas import (
    CareerSnapshot,
    AthleteProfileResponse,
    AchievementItem,
    MissionItem,
    BenchmarkItem,
    WorkoutResultSubmit,
    WorkoutResultWithXp,
    WorkoutResultRead,
    WorkoutResultCreate,
)
from application.services import (
    AthleteService,
    CareerService,
    AchievementService,
    MissionService,
    WorkoutXPService,
    WorkoutResultService,
    WorkoutService,
)
from infrastructure.auth.dependencies import get_current_user
from infrastructure.db.session import get_session
from infrastructure.db.models import (
    UserAchievementORM,
    UserCapacityProfileORM,
    UserTrainingLoadORM,
    UserBiometricORM,
    UserProgressORM,
    PhysicalCapacityORM,
    WorkoutORM,
    WorkoutExecutionORM,
    WorkoutExecutionBlockORM,
    UserSkillORM,
    UserPROM,
    MovementORM,
    WorkoutAnalysisORM,
    WorkoutBlockMovementORM,
)

router = APIRouter(dependencies=[Depends(get_current_user)])
logger = logging.getLogger("athlete.apply-impact")
SKILL_CANDIDATES = {
    "skill_row": "Row",
    "skill_wall_balls": "Wall Ball",
    "skill_kettlebell_lunge": "Kettlebell Lunge",
    "skill_burpee_box_jump_over": "Burpee Box Jump Over",
}
PR_TIME_TYPES = {"time"}
PR_TYPES_ORDER = {"BEST_TIME", "BEST_PACE", "MAX_REPS", "1RM", "3RM", "5RM"}


@router.get("/career", response_model=CareerSnapshot)
def get_career(session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    service = CareerService(session)
    return service.snapshot(current_user.id)


@router.get("/profile", response_model=AthleteProfileResponse)
def get_profile(session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    service = AthleteService(session)
    profile = service.profile(current_user.id)
    biometrics_row = profile["biometrics"]
    biometrics = None
    if biometrics_row:
        biometrics = {
            "measured_at": biometrics_row.measured_at,
            "hr_rest": float(biometrics_row.hr_rest) if biometrics_row.hr_rest is not None else None,
            "hr_avg": float(biometrics_row.hr_avg) if biometrics_row.hr_avg is not None else None,
            "hr_max": float(biometrics_row.hr_max) if biometrics_row.hr_max is not None else None,
            "vo2_est": float(biometrics_row.vo2_est) if biometrics_row.vo2_est is not None else None,
            "hrv": float(biometrics_row.hrv) if biometrics_row.hrv is not None else None,
            "sleep_hours": float(biometrics_row.sleep_hours) if biometrics_row.sleep_hours is not None else None,
            "fatigue_score": float(biometrics_row.fatigue_score) if biometrics_row.fatigue_score is not None else None,
            "recovery_time_hours": float(biometrics_row.recovery_time_hours) if biometrics_row.recovery_time_hours is not None else None,
        }
    return AthleteProfileResponse(
        career=profile["career"],
        capacities=[
            {
                "capacity": cp.capacity.name if cp.capacity else str(cp.capacity_id),
                "value": cp.value,
                "measured_at": cp.measured_at,
            }
            for cp in profile["capacities"]
        ],
        skills=[
            {"movement": sk.movement.name if sk.movement else "", "score": float(sk.skill_score), "measured_at": sk.measured_at}
            for sk in profile["skills"]
        ],
        biometrics=biometrics,
        training_load=[
            {
                "load_date": tl.load_date,
                "acute_load": float(tl.acute_load) if tl.acute_load is not None else None,
                "chronic_load": float(tl.chronic_load) if tl.chronic_load is not None else None,
                "load_ratio": float(tl.load_ratio) if tl.load_ratio is not None else None,
            }
            for tl in profile["training_load"]
        ],
        prs=[
            {
                "movement": pr.movement.name if pr.movement else "",
                "pr_type": pr.pr_type,
                "value": float(pr.value),
                "unit": pr.unit,
                "achieved_at": pr.achieved_at,
            }
            for pr in profile["prs"]
        ],
        achievements=[
            AchievementItem(
                id=ua.id,
                code=ua.achievement.code,
                name=ua.achievement.name,
                description=ua.achievement.description,
                category=ua.achievement.category,
                xp_reward=float(ua.achievement.xp_reward or 0),
                icon_url=ua.achievement.icon_url,
                unlocked_at=ua.unlocked_at,
            )
            for ua in session.query(UserAchievementORM).filter(UserAchievementORM.user_id == current_user.id).all()
        ],
        missions=[
            MissionItem(
                id=um.id,
                mission_id=um.mission_id,
                type=um.mission.type if um.mission else "",
                title=um.mission.title if um.mission else "",
                description=um.mission.description if um.mission else "",
                xp_reward=float(um.mission.xp_reward or 0) if um.mission else 0,
                status=um.status,
                progress_value=float(um.progress_value or 0),
                target_value=(um.mission.condition_json or {}).get("target") if um.mission else None,
                expires_at=um.expires_at,
                completed_at=um.completed_at,
            )
            for um in profile["missions"]
        ],
        benchmarks=[
            BenchmarkItem(
                capacity=bench.capacity.name if bench.capacity else "",
                percentile=bench.percentile_90 or bench.percentile_50,
                level=bench.athlete_level_id,
            )
            for bench in profile["benchmarks"]
        ],
    )


@router.get("/achievements", response_model=List[AchievementItem])
def achievements(session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    achievements_rows = (
        session.query(UserAchievementORM)
        .filter(UserAchievementORM.user_id == current_user.id)
        .all()
    )
    return [
        AchievementItem(
            id=ua.id,
            code=ua.achievement.code,
            name=ua.achievement.name,
            description=ua.achievement.description,
            category=ua.achievement.category,
            xp_reward=float(ua.achievement.xp_reward or 0),
            icon_url=ua.achievement.icon_url,
            unlocked_at=ua.unlocked_at,
        )
        for ua in achievements_rows
    ]


@router.get("/missions", response_model=List[MissionItem])
def missions(session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    mission_service = MissionService(session)
    missions_rows = mission_service.assign_active(current_user.id)
    return [
        MissionItem(
            id=um.id,
            mission_id=um.mission_id,
            type=um.mission.type if um.mission else "",
            title=um.mission.title if um.mission else "",
            description=um.mission.description if um.mission else "",
            xp_reward=float(um.mission.xp_reward or 0) if um.mission else 0,
            status=um.status,
            progress_value=float(um.progress_value or 0),
            target_value=(um.mission.condition_json or {}).get("target") if um.mission else None,
            expires_at=um.expires_at,
            completed_at=um.completed_at,
        )
        for um in missions_rows
    ]


@router.get("/benchmarks", response_model=List[BenchmarkItem])
def benchmarks(session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    athlete_service = AthleteService(session)
    profile = athlete_service.profile(current_user.id)
    benchmarks_rows = profile["benchmarks"]
    return [
        BenchmarkItem(
            capacity=bench.capacity.name if bench.capacity else "",
            percentile=bench.percentile_90 or bench.percentile_50,
            level=bench.athlete_level_id,
        )
        for bench in benchmarks_rows
    ]


@router.post("/workouts/{workout_id}/result", response_model=WorkoutResultWithXp, status_code=status.HTTP_201_CREATED)
def submit_result(
    workout_id: int,
    payload: WorkoutResultSubmit,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """
    Guarda un resultado de WOD. Soporta:
    - method="total": usa total_time_sec.
    - method="by_blocks": usa block_times_sec y suma como total.
    Además, registra la ejecución y tiempos por bloque si existen.
    """
    logger.info(
        "[submit_result] user=%s workout=%s method=%s total=%s blocks=%s",
        current_user.id,
        workout_id,
        payload.method,
        payload.total_time_sec,
        payload.block_times_sec if payload.block_times_sec else None,
    )
    if payload.method not in {"total", "by_blocks"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid method")

    block_times = list(payload.block_times_sec or [])
    total_seconds = payload.total_time_sec
    workout_row = session.query(WorkoutORM).filter(WorkoutORM.id == workout_id).first()
    ordered_blocks = sorted(workout_row.blocks or [], key=lambda b: b.position or 0) if workout_row else []
    if payload.method == "by_blocks":
        if not block_times:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="block_times_sec required for by_blocks")
        if any((t is None or t <= 0) for t in block_times):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="block_times_sec must be positive")
        total_seconds = sum(block_times)
    if payload.method == "total":
        if total_seconds is None or total_seconds <= 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="total_time_sec required for total")

    # Persistir ejecución y bloques si aplica
    execution_id = None
    impact_snapshot = {
        "acute_load": float(total_seconds or 0),
        "chronic_load": float(total_seconds or 0) * 0.65,
    }
    execution = (
        session.query(WorkoutExecutionORM)
        .filter(
            WorkoutExecutionORM.user_id == current_user.id,
            WorkoutExecutionORM.workout_id == workout_id,
            func.date(WorkoutExecutionORM.executed_at) == date.today(),
        )
        .order_by(WorkoutExecutionORM.executed_at.desc())
        .first()
    )

    if execution:
        # Reutiliza la ejecucion del dia: solo actualiza notas e impacto
        raw_json = execution.raw_ocr_json if isinstance(execution.raw_ocr_json, dict) else {}
        raw_json["block_times_sec"] = block_times if payload.method == "by_blocks" else raw_json.get("block_times_sec")
        raw_json["impact"] = impact_snapshot
        execution.raw_ocr_json = raw_json
        execution.notes = f"{execution.notes or ''} | method={payload.method}".strip(" |")
        if not execution.total_time_seconds:
            execution.total_time_seconds = total_seconds
        execution_id = execution.id
        skip_training_load = True
    else:
        skip_training_load = False
        execution = WorkoutExecutionORM(
            workout_id=workout_id,
            user_id=current_user.id,
            total_time_seconds=total_seconds,
            notes=f"method={payload.method}",
            raw_ocr_json={
              "block_times_sec": block_times if payload.method == 'by_blocks' else None,
              "impact": impact_snapshot
            },
        )
        session.add(execution)
        session.flush()
        execution_id = execution.id

    if payload.method == "by_blocks":
        # mapear blocks por orden de posición
        if ordered_blocks and len(block_times) != len(ordered_blocks):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="block_times_sec length must match workout blocks",
            )
        for idx, time_sec in enumerate(block_times):
            block_id = ordered_blocks[idx].id if ordered_blocks and idx < len(ordered_blocks) else None
            session.add(
                WorkoutExecutionBlockORM(
                    execution_id=execution_id,
                    workout_block_id=block_id,
                    time_seconds=time_sec,
                )
            )

    # actualizar carga diaria básica
    tl_today = (
        session.query(UserTrainingLoadORM)
        .filter(UserTrainingLoadORM.user_id == current_user.id, UserTrainingLoadORM.load_date == date.today())
        .with_for_update()
        .first()
    )
    if not skip_training_load:
        if tl_today:
            base_acute = float(tl_today.acute_load or 0)
            base_chronic = float(tl_today.chronic_load or 0)
            tl_today.acute_load = base_acute + float(impact_snapshot["acute_load"])
            tl_today.chronic_load = base_chronic + float(impact_snapshot["chronic_load"])
            tl_today.load_ratio = float(tl_today.acute_load) / float(tl_today.chronic_load or tl_today.acute_load or 1)
        else:
            tl_today = UserTrainingLoadORM(
                user_id=current_user.id,
                load_date=date.today(),
                acute_load=float(impact_snapshot["acute_load"]),
                chronic_load=float(impact_snapshot["chronic_load"]),
                load_ratio=1.0,
                notes=f"WOD {workout_id} metodo {payload.method}",
            )
            session.add(tl_today)

    session.commit()

    result_service = WorkoutResultService(session)
    created = result_service.create(
        WorkoutResultCreate(
            workout_id=workout_id,
            user_id=current_user.id,
            time_seconds=total_seconds,
            difficulty=payload.difficulty,
            rating=payload.rating,
            comment=payload.comment or (f"method={payload.method}" if payload.method else None),
        )
    )
    if not created:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User or workout not found")
    xp_service = WorkoutXPService(session)
    xp_awarded, snapshot = xp_service.award_for_result(
        current_user.id, workout_id, total_seconds, payload.difficulty
    )
    achievement_service = AchievementService(session)
    unlocked = achievement_service.evaluate_level(current_user.id, snapshot["level"])
    mission_service = MissionService(session)
    new_pr = _update_prs_from_execution(
        session=session,
        user_id=current_user.id,
        workout=workout_row,
        ordered_blocks=ordered_blocks,
        block_times=block_times if payload.method == "by_blocks" else [],
        total_seconds=total_seconds,
    )
    completed, _ = mission_service.update_progress_for_workout(current_user.id, new_pr=new_pr)
    response = WorkoutResultWithXp(
        result=created,
        xp_awarded=xp_awarded,
        xp_total=snapshot["xp_total"],
        level=snapshot["level"],
        progress_pct=snapshot["progress_pct"],
        achievements_unlocked=unlocked,
        missions_completed=completed,
    )
    return response


def _capacity_code_map(session: Session) -> Dict[str, int]:
    mapping: Dict[str, int] = {}
    rows = session.query(PhysicalCapacityORM).all()
    for row in rows:
        key = (row.code or "").strip().lower()
        if not key:
            continue
        mapping[key] = row.id
    return mapping


def _canonical_to_db_capacity_code(canonical: str) -> Optional[str]:
    key = (canonical or "").lower().strip()
    key = (
        key.replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("-", " ")
        .replace("_", " ")
    )
    mapping = {
        "resistance": "resistencia",
        "resistencia": "resistencia",
        "strength": "fuerza",
        "fuerza": "fuerza",
        "metcon": "metcon",
        "gymnastics": "gimnásticos",
        "gimnastics": "gimnásticos",
        "gimnasticos": "gimnásticos",
        "gimnastico": "gimnásticos",
        "velocidad": "velocidad",
        "speed": "velocidad",
        "potencia": "potencia",
        "power": "potencia",
        "carga muscular": "carga muscular",
        "muscular load": "carga muscular",
    }
    return mapping.get(key)


def _map_profile_to_metrics(profile: dict) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for cp in profile.get("capacities", []):
        code = None
        if hasattr(cp, "capacity") and getattr(cp, "capacity") is not None:
            cap_obj = getattr(cp, "capacity")
            code = getattr(cap_obj, "code", None) or getattr(cap_obj, "name", None)
        elif isinstance(cp, dict):
            code = cp.get("capacity") if isinstance(cp.get("capacity"), str) else None
        code = (code or "").lower()
        canonical = {
            "resistencia": "resistance",
            "fuerza": "strength",
            "metcon": "metcon",
            "gimnásticos": "gymnastics",
            "velocidad": "speed",
        }.get(code)
        if canonical:
            value = getattr(cp, "value", None)
            if value is None and isinstance(cp, dict):
                value = cp.get("value")
            if value is not None:
                out[canonical] = float(value)
    biom = profile.get("biometrics")
    if biom:
        def _get(attr):
            if isinstance(biom, dict):
                return biom.get(attr)
            return getattr(biom, attr, None)

        if _get("fatigue_score") is not None:
            out["fatigue_score"] = float(_get("fatigue_score"))
        if _get("hr_rest") is not None:
            out["hr_rest"] = float(_get("hr_rest"))
        if _get("hr_avg") is not None:
            out["hr_avg"] = float(_get("hr_avg"))
        if _get("hr_max") is not None:
            out["hr_max"] = float(_get("hr_max"))
        if _get("vo2_est") is not None:
            out["vo2_est"] = float(_get("vo2_est"))
        if _get("hrv") is not None:
            out["hrv"] = float(_get("hrv"))
        if _get("sleep_hours") is not None:
            out["sleep_hours"] = float(_get("sleep_hours"))
    tl_rows = profile.get("training_load", [])
    if tl_rows:
        latest_tl = tl_rows[0]
        getter = (lambda attr: latest_tl.get(attr)) if isinstance(latest_tl, dict) else (lambda attr: getattr(latest_tl, attr, None))
        if getter("acute_load") is not None:
            out["acute_load"] = float(getter("acute_load"))
        if getter("chronic_load") is not None:
            out["chronic_load"] = float(getter("chronic_load"))
        if getter("load_ratio") is not None:
            out["load_ratio"] = float(getter("load_ratio"))
    return out


def _skill_movement_map(session: Session) -> Dict[str, int]:
    mapping: Dict[str, int] = {}
    for key, name in SKILL_CANDIDATES.items():
        mv = session.query(MovementORM).filter(func.lower(MovementORM.name) == name.lower()).first()
        if mv:
            mapping[key] = mv.id
    return mapping


def _infer_skill_deltas_from_workout(workout: WorkoutORM) -> Dict[str, float]:
    """
    Genera un delta minimo de skill a partir de los movimientos del WOD
    cuando el análisis no trae claves skill_*.
    """
    deltas: Dict[str, float] = {}
    if not workout or not workout.blocks:
        return deltas
    for block in workout.blocks or []:
        for mv in block.movements or []:
            name = (mv.movement.name if mv.movement else "").lower()
            for key, target in SKILL_CANDIDATES.items():
                if name == target.lower():
                    deltas[key] = deltas.get(key, 0.0) + 2.0
    return deltas


def _best_pr_row(session: Session, user_id: int, movement_id: int, pr_type: str) -> Optional[UserPROM]:
    query = (
        session.query(UserPROM)
        .filter(UserPROM.user_id == user_id, UserPROM.movement_id == movement_id, UserPROM.pr_type == pr_type)
    )
    if pr_type == "time":
        return query.order_by(UserPROM.value.asc()).first()
    return query.order_by(UserPROM.value.desc()).first()


def _register_pr_if_better(
    session: Session, user_id: int, movement_id: int, pr_type: str, value: float, unit: Optional[str]
) -> bool:
    existing = _best_pr_row(session, user_id, movement_id, pr_type)
    is_better = False
    if not existing:
        is_better = True
    elif pr_type == "time":
        try:
            is_better = float(value) < float(existing.value)
        except Exception:
            is_better = False
    else:
        try:
            is_better = float(value) > float(existing.value)
        except Exception:
            is_better = False
    if not is_better:
        return False
    session.add(
        UserPROM(
            user_id=user_id,
            movement_id=movement_id,
            pr_type=pr_type,
            value=value,
            unit=unit or ("s" if pr_type == "time" else None),
            achieved_at=datetime.utcnow(),
        )
    )
    return True


def _pr_candidates_from_execution(
    workout: Optional[WorkoutORM],
    ordered_blocks: List[Any],
    block_times: List[float],
    total_seconds: Optional[float],
) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    if block_times and ordered_blocks and len(block_times) == len(ordered_blocks):
        for idx, block in enumerate(ordered_blocks):
            if not block.movements or len(block.movements) != 1:
                continue
            mv = block.movements[0]
            if not mv or not mv.movement_id:
                continue
            time_val = block_times[idx]
            if time_val is None or time_val <= 0:
                continue
            candidates.append({"movement_id": mv.movement_id, "pr_type": "time", "value": float(time_val), "unit": "s"})
    if (not block_times) and total_seconds and total_seconds > 0 and workout:
        if len(ordered_blocks) == 1 and ordered_blocks[0].movements and len(ordered_blocks[0].movements) == 1:
            mv = ordered_blocks[0].movements[0]
            if mv and mv.movement_id:
                candidates.append({"movement_id": mv.movement_id, "pr_type": "time", "value": float(total_seconds), "unit": "s"})
    return candidates


def _load_skill_note(existing_note: Optional[str]) -> Dict[str, Any]:
    import json
    if not existing_note:
        return {}
    try:
        parsed = json.loads(existing_note)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _skill_primary_metric(totals: Dict[str, float]) -> tuple[str, float]:
    for key in ["total_kg", "total_reps", "total_meters", "total_cals", "total_seconds"]:
        val = float(totals.get(key) or 0)
        if val > 0:
            return key, val
    return "total_seconds", float(totals.get("total_seconds") or 0)


def _aggregate_skill_for_movement(
    session: Session,
    user_id: int,
    movement_id: int,
    inc: Dict[str, float],
    source: str = "wod_apply",
) -> None:
    now = datetime.utcnow()
    existing = (
        session.query(UserSkillORM)
        .filter(UserSkillORM.user_id == user_id, UserSkillORM.movement_id == movement_id)
        .order_by(UserSkillORM.measured_at.desc())
        .first()
    )
    totals = _load_skill_note(existing.note if existing else None)
    totals["total_reps"] = float(totals.get("total_reps") or 0) + float(inc.get("reps") or 0)
    totals["total_kg"] = float(totals.get("total_kg") or 0) + float(inc.get("kg") or 0)
    totals["total_meters"] = float(totals.get("total_meters") or 0) + float(inc.get("meters") or 0)
    totals["total_cals"] = float(totals.get("total_cals") or 0) + float(inc.get("cals") or 0)
    totals["total_seconds"] = float(totals.get("total_seconds") or 0) + float(inc.get("seconds") or 0)
    totals["last_increment"] = {
        "reps": inc.get("reps", 0),
        "kg": inc.get("kg", 0),
        "meters": inc.get("meters", 0),
        "cals": inc.get("cals", 0),
        "seconds": inc.get("seconds", 0),
    }
    totals["source"] = source
    totals["updated_at"] = now.isoformat()
    primary_metric, primary_value = _skill_primary_metric(totals)
    totals["primary_metric"] = primary_metric
    totals["primary_value"] = primary_value
    skill_score = primary_value

    import json

    if existing:
        existing.skill_score = skill_score
        existing.note = json.dumps(totals)
        existing.measured_at = now
        session.add(existing)
    else:
        session.add(
            UserSkillORM(
                user_id=user_id,
                movement_id=movement_id,
                skill_score=skill_score,
                note=json.dumps(totals),
                measured_at=now,
            )
        )


def _extract_movements_payload(workout: WorkoutORM) -> List[WorkoutBlockMovementORM]:
    if not workout or not workout.blocks:
        return []
    blocks = sorted(workout.blocks or [], key=lambda b: b.position or 0)
    mv_rows: List[WorkoutBlockMovementORM] = []
    for blk in blocks:
        for mv in blk.movements or []:
            mv_rows.append(mv)
    return mv_rows


def _movement_increment(mv: WorkoutBlockMovementORM) -> Dict[str, float]:
    reps = float(mv.reps or 0)
    load = float(mv.load or 0)
    inc = {
        "reps": reps,
        "kg": reps * load if reps and load else 0.0,
        "meters": float(mv.distance_meters or 0),
        "seconds": float(mv.duration_seconds or 0),
        "cals": float(mv.calories or 0),
    }
    return inc


def _upsert_skill_aggregates(session: Session, user_id: int, workout: WorkoutORM) -> int:
    rows = _extract_movements_payload(workout)
    if not rows:
        return 0
    count = 0
    for mv in rows:
        if not mv.movement_id:
            continue
        inc = _movement_increment(mv)
        if all(v == 0 or v is None for v in inc.values()):
            continue
        _aggregate_skill_for_movement(session, user_id, mv.movement_id, inc)
        count += 1
    if count:
        session.flush()
    return count


def _better_pr(pr_type: str, new_value: float, old_value: float) -> bool:
    if pr_type in {"BEST_TIME", "BEST_PACE"}:
        return new_value < old_value
    return new_value > old_value


def _upsert_pr(
    session: Session,
    user_id: int,
    movement_id: int,
    pr_type: str,
    value: float,
    unit: Optional[str],
) -> bool:
    existing = (
        session.query(UserPROM)
        .filter(UserPROM.user_id == user_id, UserPROM.movement_id == movement_id, UserPROM.pr_type == pr_type)
        .order_by(UserPROM.achieved_at.desc())
        .first()
    )
    now = datetime.utcnow()
    if not existing:
        session.add(UserPROM(user_id=user_id, movement_id=movement_id, pr_type=pr_type, value=value, unit=unit, achieved_at=now))
        return True
    try:
        if _better_pr(pr_type, value, float(existing.value)):
            existing.value = value
            existing.unit = unit or existing.unit
            existing.achieved_at = now
            session.add(existing)
            return True
    except Exception:
        return False
    return False


def _update_prs_from_execution(
    session: Session,
    user_id: int,
    workout: Optional[WorkoutORM],
    ordered_blocks: List[Any],
    block_times: List[float],
    total_seconds: Optional[float],
) -> bool:
    candidates = _pr_candidates_from_execution(workout, ordered_blocks, block_times, total_seconds)
    created = 0
    for item in candidates:
        if _register_pr_if_better(
            session=session,
            user_id=user_id,
            movement_id=item["movement_id"],
            pr_type=item["pr_type"],
            value=item["value"],
            unit=item.get("unit"),
        ):
            created += 1
    if created:
        session.commit()
        logger.info("[submit_result][pr] user=%s workout=%s new_prs=%s", user_id, workout.id if workout else None, created)
    return created > 0


def _skill_rows(session: Session, athlete_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    query = (
        session.query(UserSkillORM)
        .filter(UserSkillORM.user_id == athlete_id)
        .join(MovementORM, MovementORM.id == UserSkillORM.movement_id)
        .order_by(UserSkillORM.skill_score.desc())
    )
    if limit:
        query = query.limit(limit)
    rows = query.all()
    import json
    out = [
        {
            "key": sk.id,
            "name": sk.movement.name if sk.movement else "",
            "category": sk.movement.category if sk.movement else None,
            "unit": (_load_skill_note(sk.note).get("primary_metric") if sk.note else None) or "pts",
            "value": float(sk.skill_score),
            "measured_at": sk.measured_at,
            "breakdown": _load_skill_note(sk.note) if sk.note else {},
        }
        for sk in rows
    ]
    logger.info("[skills][read] athlete=%s count=%s limit=%s", athlete_id, len(out), limit)
    return out


def _pr_rows(session: Session, athlete_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    query = (
        session.query(UserPROM)
        .filter(UserPROM.user_id == athlete_id)
        .join(MovementORM, MovementORM.id == UserPROM.movement_id)
    )
    # ordenar: tiempos asc, otros desc
    query = query.order_by(
        case((UserPROM.pr_type.in_(PR_TIME_TYPES), UserPROM.value), else_=-UserPROM.value).asc()
    )
    if limit:
        query = query.limit(limit)
    rows = query.all()
    out = [
        {
            "name": pr.movement.name if pr.movement else "",
            "type": pr.pr_type,
            "unit": pr.unit or ("s" if pr.pr_type in PR_TIME_TYPES else None),
            "value": float(pr.value),
            "achieved_at": pr.achieved_at,
        }
        for pr in rows
    ]
    logger.info("[prs][read] athlete=%s count=%s limit=%s", athlete_id, len(out), limit)
    return out


def _overview_payload(session: Session, athlete_id: int, top_limit: int = 5) -> Dict[str, Any]:
    top_skills = _skill_rows(session, athlete_id, limit=top_limit)
    top_prs = _pr_rows(session, athlete_id, limit=top_limit)
    # aggregate totals from all skills breakdown
    all_skills = _skill_rows(session, athlete_id, limit=None)
    totals = {
        "skills_total": sum(item["value"] for item in all_skills),
        "prs_total": len(top_prs),
        "total_reps": sum((item.get("breakdown") or {}).get("total_reps", 0) for item in all_skills),
        "total_kg": sum((item.get("breakdown") or {}).get("total_kg", 0) for item in all_skills),
        "total_meters": sum((item.get("breakdown") or {}).get("total_meters", 0) for item in all_skills),
        "total_cals": sum((item.get("breakdown") or {}).get("total_cals", 0) for item in all_skills),
        "total_seconds": sum((item.get("breakdown") or {}).get("total_seconds", 0) for item in all_skills),
    }
    logger.info("[stats][overview] athlete=%s skills=%s prs=%s", athlete_id, len(top_skills), len(top_prs))
    return {"topSkills": top_skills, "topPrs": top_prs, "totals": totals}


def _parse_capacity_focus(capacity_focus: List[dict]) -> Dict[str, float]:
    def _parse_value(val_raw) -> float:
        if isinstance(val_raw, (int, float)):
            return float(val_raw)
        if isinstance(val_raw, str):
            # soporta "75/100", "75%", "75", "75.0"
            if "/" in val_raw:
                head = val_raw.split("/", 1)[0]
                try:
                    return float(head)
                except Exception:
                    return 0.0
            cleaned = val_raw.replace("%", "")
            digits = "".join(ch for ch in cleaned if ch.isdigit() or ch == ".")
            try:
                return float(digits)
            except Exception:
                return 0.0
        return 0.0

    out: Dict[str, float] = {}
    for item in capacity_focus or []:
        cap = (item.get("capacity") or "").lower()
        val_raw = item.get("emphasis") or item.get("value")
        val = _parse_value(val_raw)
        if cap:
            out[cap] = val
    return out


def _level_fatigue_factor(level: Optional[int]) -> float:
    """
    Factor progresivo para fatiga: nivel 1 ~2.5x y decrece linealmente hasta 1.0x en nivel 50.
    """
    if level is None or level <= 0:
        return 2.5
    high = 2.5
    low = 1.0
    span = max(1, 50 - 1)
    factor = high - (min(level, 50) - 1) * ((high - low) / span)
    return max(low, round(factor, 3))


def _ensure_impact_defaults(
    analysis_row: WorkoutAnalysisORM, workout: WorkoutORM, current_impact: Dict[str, Any], incoming: Dict[str, Any]
) -> Dict[str, float]:
    def _parse_number(val) -> Optional[float]:
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            digits = "".join(ch for ch in val if ch.isdigit() or ch in {".", "-", ","})
            digits = digits.replace(",", ".")
            if digits:
                try:
                    return float(digits)
                except Exception:
                    return None
        return None

    impact: Dict[str, float] = {}
    # merge existing numeric impact
    for k, v in (current_impact or {}).items():
        parsed = _parse_number(v)
        if parsed is not None:
            impact[k] = parsed
    # incoming overrides
    for k, v in (incoming or {}).items():
        parsed = _parse_number(v)
        if parsed is not None:
            impact[k] = parsed

    analysis_json = analysis_row.analysis_json if isinstance(analysis_row.analysis_json, dict) else {}

    # capacities: prefer explicit, fall back to capacity_focus then workout.capacities
    has_capacity = any(_canonical_to_db_capacity_code(k) for k in impact.keys())
    if not has_capacity:
        for k, v in _parse_capacity_focus(analysis_json.get("capacity_focus", [])).items():
            impact.setdefault(k, float(v))
        if workout and getattr(workout, "capacities", None):
            for cp in workout.capacities or []:
                cap_name = None
                if hasattr(cp, "capacity") and cp.capacity:
                    cap_name = getattr(cp.capacity, "code", None) or getattr(cp.capacity, "name", None) or getattr(
                        cp.capacity, "value", None
                    )
                cap_name = cap_name or getattr(cp, "capacity", None)
                if cap_name:
                    key = str(cap_name).lower()
                    impact.setdefault(key, float(getattr(cp, "value", 0) or 0))

    # fatigue
    fatigue = impact.get("fatigue_score")
    if fatigue is None:
        fatigue = _parse_number(analysis_json.get("fatigue_score"))
    if fatigue is None:
        fatigue = 10.0
    impact["fatigue_score"] = float(fatigue)

    # fallback: si seguimos sin capacidades, infiere una genérica basada en dominio o metcon
    if not any(_canonical_to_db_capacity_code(k) for k in impact.keys()):
        domain = (getattr(workout, "domain", None) or "").lower()
        if "fuerza" in domain or "strength" in domain:
            impact["fuerza"] = 5.0
        elif "resistencia" in domain or "endurance" in domain:
            impact["resistencia"] = 5.0
        elif "potencia" in domain or "power" in domain:
            impact["potencia"] = 5.0
        else:
            impact["metcon"] = 5.0

    # loads
    acute = _parse_number(impact.get("acute_load"))
    chronic = _parse_number(impact.get("chronic_load"))
    if acute is None or chronic is None:
        session_load_val = _parse_number(analysis_json.get("session_load"))
        if session_load_val is None and getattr(workout, "metadata_rel", None):
            session_load_val = _parse_number(getattr(workout.metadata_rel, "session_load", None))
        base_load = session_load_val if session_load_val is not None else fatigue * 8.0
        acute = acute if acute is not None else base_load
        chronic = chronic if chronic is not None else max(1.0, round(acute * 0.65, 2))
        impact["acute_load"] = float(acute)
        impact["chronic_load"] = float(chronic)
    if "load_ratio" not in impact and impact.get("chronic_load"):
        try:
            impact["load_ratio"] = round(float(impact["acute_load"]) / float(impact["chronic_load"]), 2)
        except Exception:
            pass

    return impact


@router.post("/workouts/{workout_id}/apply-impact")
def apply_workout_impact(
    workout_id: int,
    payload: Optional[dict] = Body(default=None),
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """
    Aplica el impacto del WOD al perfil del atleta. Idempotente.
    - Si se pasa analysis_id en el cuerpo, se usa.
    - Si no, se busca el ultimo analysis de ese workout para el usuario; si no existe, se crea
      a partir de un analisis ad-hoc del workout para no dejar el flujo roto.
    - Si no hay athlete_impact, se genera un impacto minimo a partir de capacity_focus y fatigue_score.
    """
    analysis_id = None
    incoming_impact: Dict[str, Any] = {}
    if isinstance(payload, dict):
        analysis_id = payload.get("analysis_id") or payload.get("id")
        incoming_impact = payload.get("athlete_impact") or payload.get("impact") or {}

    workout_service = WorkoutService(session)
    workout = session.get(WorkoutORM, workout_id)
    if not workout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")

    query = session.query(WorkoutAnalysisORM).filter(WorkoutAnalysisORM.user_id == current_user.id)
    if analysis_id:
        query = query.filter(WorkoutAnalysisORM.id == int(analysis_id))
    else:
        query = query.filter(WorkoutAnalysisORM.workout_id == workout_id).order_by(WorkoutAnalysisORM.created_at.desc())

    analysis_row: WorkoutAnalysisORM | None = query.with_for_update().first()

    if not analysis_row:
        analysis_json = workout_service.analysis(workout_id)
        if not analysis_json:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cannot compute analysis for this workout")
        base_impact: Dict[str, float] = {}
        base_impact.update(_parse_capacity_focus(analysis_json.get("capacity_focus", [])))
        if analysis_json.get("fatigue_score") is not None:
            base_impact["fatigue_score"] = float(analysis_json["fatigue_score"])

        analysis_row = WorkoutAnalysisORM(
            workout_id=workout_id,
            user_id=current_user.id,
            analysis_json=analysis_json,
            athlete_impact=base_impact,
            applied=False,
        )
        session.add(analysis_row)
        session.flush()

    impact_delta = _ensure_impact_defaults(analysis_row, workout, analysis_row.athlete_impact or {}, incoming_impact)
    analysis_row.athlete_impact = impact_delta
    logger.info(
        "[apply-impact] start user=%s workout=%s analysis=%s impact_keys=%s",
        current_user.id,
        workout_id,
        analysis_row.id,
        list(impact_delta.keys()),
    )
    # aggregate skills by movement exposure
    skills_count = _upsert_skill_aggregates(session, current_user.id, workout)
    if skills_count:
        logger.info("[apply-impact][skills] user=%s workout=%s updated_skills=%s", current_user.id, workout_id, skills_count)

    if not impact_delta:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing athlete impact in analysis")

    if analysis_row.applied:
        logger.info("[apply-impact] Impact already applied for user=%s analysis=%s", current_user.id, analysis_row.id)
        profile = AthleteService(session).profile(current_user.id)
        metrics = _map_profile_to_metrics(profile)
        applied_analysis = {
            **(analysis_row.analysis_json or {}),
            "id": analysis_row.id,
            "workout_id": analysis_row.workout_id,
            "user_id": analysis_row.user_id,
            "applied": True,
            "applied_at": analysis_row.applied_at.isoformat() if analysis_row.applied_at else None,
            "athlete_impact": impact_delta,
        }
        return {"analysis": applied_analysis, "updated_profile": metrics, "impact": impact_delta}

    workout: WorkoutORM | None = session.get(WorkoutORM, analysis_row.workout_id)
    if not workout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found for analysis")

    analysis_id = analysis_row.id
    # estimadores para XP
    estimated_time = analysis_row.analysis_json.get("avg_time_seconds") if isinstance(analysis_row.analysis_json, dict) else None
    estimated_diff = None
    try:
        estimated_diff = int(analysis_row.analysis_json.get("fatigue_score")) if isinstance(analysis_row.analysis_json, dict) else None
    except Exception:
        estimated_diff = None
    cap_code_map = _capacity_code_map(session)
    skill_map = _skill_movement_map(session)
    skill_inferred = _infer_skill_deltas_from_workout(workout)
    applied_metrics: Dict[str, Any] = {}
    now = datetime.utcnow()
    delta_acute = float(impact_delta.get("acute_load", 0))
    delta_chronic = float(impact_delta.get("chronic_load", 0))
    delta_ratio = impact_delta.get("load_ratio")

    # ajuste de fatiga progresivo según nivel del usuario (1..50)
    progress_row = session.query(UserProgressORM).filter(UserProgressORM.user_id == current_user.id).first()
    level_factor_fatigue = _level_fatigue_factor(progress_row.level if progress_row else None)
    if impact_delta.get("fatigue_score") is not None:
        impact_delta["fatigue_score"] = float(impact_delta["fatigue_score"]) * level_factor_fatigue

    for key, delta in impact_delta.items():
        if key in {"fatigue_score", "acute_load", "chronic_load", "load_ratio"} or str(key).startswith("skill_"):
            continue
        canonical_code = _canonical_to_db_capacity_code(key)
        if not canonical_code:
            logger.warning("[apply-impact] Capacity key without mapping: %s", key)
            continue
        cap_id = cap_code_map.get(canonical_code.lower())
        if not cap_id:
            logger.warning("[apply-impact] Capacity %s not found in DB", canonical_code)
            continue
        latest = (
            session.query(UserCapacityProfileORM)
            .filter(UserCapacityProfileORM.user_id == current_user.id, UserCapacityProfileORM.capacity_id == cap_id)
            .order_by(UserCapacityProfileORM.measured_at.desc())
            .first()
        )
        base_value = float(latest.value) if latest else 0.0
        new_value = _clamp_capacity(base_value + delta)
        applied_metrics[key] = new_value
        session.add(
            UserCapacityProfileORM(
                user_id=current_user.id,
                capacity_id=cap_id,
                value=int(round(new_value)),
                measured_at=now,
            )
        )

    fatigue_delta = impact_delta.get("fatigue_score")
    if fatigue_delta is not None:
        # factor por nivel y cantidad de sesiones en el día
        progress_row = session.query(UserProgressORM).filter(UserProgressORM.user_id == current_user.id).first()
        level_factor = 1.0
        if progress_row:
            if progress_row.level <= 2:
                level_factor = 2.2  # principiantes sienten más
            elif progress_row.level <= 4:
                level_factor = 1.5
            else:
                level_factor = 1.1
        execs_today = (
            session.query(WorkoutExecutionORM)
            .filter(
                WorkoutExecutionORM.user_id == current_user.id,
                func.date(WorkoutExecutionORM.executed_at) == date.today(),
            )
            .count()
        )
        latest_bio = (
            session.query(UserBiometricORM)
            .filter(UserBiometricORM.user_id == current_user.id)
            .order_by(UserBiometricORM.measured_at.desc())
            .first()
        )
        base_fatigue = float(latest_bio.fatigue_score) if latest_bio and latest_bio.fatigue_score is not None else 0.0

        # aumento base ponderado por nivel y número de WODs
        fatigue_gain = float(fatigue_delta) * level_factor * (1 + execs_today * 0.6)
        # mínimo para no infravalorar
        fatigue_gain = max(fatigue_gain, float(fatigue_delta) * 1.5)
        # impacto por carga
        fatigue_gain += max(delta_acute, 0) * 0.5
        fatigue_gain += max(delta_chronic, 0) * 0.25
        # boost por cada WOD extra en el día
        if execs_today > 1:
            fatigue_gain += 15 * (execs_today - 1)

        # el campo es Numeric(4,2) en DB: max ~99.99, mantenemos margen
        new_fatigue = min(99.0, base_fatigue + fatigue_gain)
        session.add(
            UserBiometricORM(
                user_id=current_user.id,
                measured_at=now,
                fatigue_score=new_fatigue,
            )
        )
        applied_metrics["fatigue_score"] = new_fatigue

    for key, mv_id in skill_map.items():
        if key not in impact_delta and key not in skill_inferred:
            continue
        delta = impact_delta.get(key) if key in impact_delta else skill_inferred.get(key)
        if delta is None:
            continue
        latest_skill = (
            session.query(UserSkillORM)
            .filter(UserSkillORM.user_id == current_user.id, UserSkillORM.movement_id == mv_id)
            .order_by(UserSkillORM.measured_at.desc())
            .first()
        )
        base_score = float(latest_skill.skill_score) if latest_skill else 0.0
        new_score = max(0.0, min(100.0, base_score + float(delta)))
        session.add(
            UserSkillORM(
                user_id=current_user.id,
                movement_id=mv_id,
                skill_score=new_score,
                note=f"Impacto WOD {workout.id}",
                measured_at=now,
            )
        )
        applied_metrics[key] = new_score

    existing_exec = (
        session.query(WorkoutExecutionORM)
        .filter(
            WorkoutExecutionORM.user_id == current_user.id,
            WorkoutExecutionORM.workout_id == workout.id,
            func.date(WorkoutExecutionORM.executed_at) == date.today(),
        )
        .order_by(WorkoutExecutionORM.executed_at.desc())
        .with_for_update()
        .first()
    )
    skip_load_update = False
    if existing_exec:
        raw_json = existing_exec.raw_ocr_json if isinstance(existing_exec.raw_ocr_json, dict) else {}
        raw_json["impact"] = impact_delta
        raw_json["analysis_id"] = analysis_id
        raw_json["impact_applied"] = True
        existing_exec.raw_ocr_json = raw_json
        existing_exec.notes = f"{existing_exec.notes or ''} | Impacto aplicado {now.isoformat()}".strip(" |")
        exec_row = existing_exec
        skip_load_update = True
    else:
        exec_row = WorkoutExecutionORM(
            workout_id=workout.id,
            user_id=current_user.id,
            executed_at=now,
            raw_ocr_json={"analysis_id": analysis_id, "impact_applied": True, "impact": impact_delta},
            notes=f"Impacto aplicado {now.isoformat()}",
        )
        session.add(exec_row)

    # si ya existia ejecucion del dia (por submit_result), no sumamos carga de nuevo
    if not skip_load_update:
        tl_today = (
            session.query(UserTrainingLoadORM)
            .filter(UserTrainingLoadORM.user_id == current_user.id, UserTrainingLoadORM.load_date == date.today())
            .with_for_update()
            .first()
        )
        tl_latest = (
            session.query(UserTrainingLoadORM)
            .filter(UserTrainingLoadORM.user_id == current_user.id)
            .order_by(UserTrainingLoadORM.load_date.desc())
            .first()
        )
        base_acute = float(tl_latest.acute_load) if tl_latest and tl_latest.acute_load is not None else 0.0
        base_chronic = float(tl_latest.chronic_load) if tl_latest and tl_latest.chronic_load is not None else 0.0
        base_ratio = float(tl_latest.load_ratio) if tl_latest and tl_latest.load_ratio is not None else None
        new_acute = base_acute + delta_acute
        new_chronic = base_chronic + delta_chronic
        computed_ratio = delta_ratio if delta_ratio is not None else (new_acute / new_chronic if new_chronic else base_ratio)
        if tl_today:
            tl_today.acute_load = new_acute
            tl_today.chronic_load = new_chronic
            tl_today.load_ratio = computed_ratio
        else:
            tl_today = UserTrainingLoadORM(
                user_id=current_user.id,
                load_date=date.today(),
                acute_load=new_acute,
                chronic_load=new_chronic,
                load_ratio=computed_ratio or 1.0,
                notes=f"Impacto WOD {workout.id} analysis {analysis_id}",
            )
            session.add(tl_today)
        applied_metrics["acute_load"] = new_acute
        applied_metrics["chronic_load"] = new_chronic
        if computed_ratio is not None:
            applied_metrics["load_ratio"] = computed_ratio
    else:
        applied_metrics["acute_load"] = delta_acute
        applied_metrics["chronic_load"] = delta_chronic
        if delta_ratio is not None:
            applied_metrics["load_ratio"] = delta_ratio

    analysis_row.applied = True
    analysis_row.applied_at = now
    session.add(analysis_row)

    # XP y nivel
    xp_awarded = 0
    career_snapshot = None
    try:
        xp_awarded, career_snapshot = WorkoutXPService(session).award_for_result(
            current_user.id,
            workout.id,
            estimated_time if isinstance(estimated_time, (int, float)) else None,
            estimated_diff if isinstance(estimated_diff, (int, float)) else None,
        )
    except Exception:
        xp_awarded = 0
        career_snapshot = CareerService(session).snapshot(current_user.id)

    session.commit()

    logger.info(
        "[apply-impact] Applied impact for user=%s workout=%s metrics_updated=%s xp=%s",
        current_user.id,
        workout.id,
        list(applied_metrics.keys()),
        xp_awarded,
    )

    profile = AthleteService(session).profile(current_user.id)
    metrics = _map_profile_to_metrics(profile)
    applied_analysis = {
        **(analysis_row.analysis_json or {}),
        "id": analysis_row.id,
        "workout_id": analysis_row.workout_id,
        "user_id": analysis_row.user_id,
        "applied": True,
        "applied_at": now.isoformat(),
        "athlete_impact": impact_delta,
    }

    return {
        "analysis": applied_analysis,
        "updated_profile": metrics,
        "impact": impact_delta,
        "xp_awarded": xp_awarded,
        "career": career_snapshot or profile.get("career"),
    }


@router.get("/{athlete_id}/skills/top")
def athlete_skills_top(athlete_id: int, limit: int = 5, session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    if current_user.id != athlete_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this athlete")
    return _skill_rows(session, athlete_id, limit=limit)


@router.get("/{athlete_id}/skills")
def athlete_skills(athlete_id: int, session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    if current_user.id != athlete_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this athlete")
    return _skill_rows(session, athlete_id, limit=None)


@router.get("/{athlete_id}/prs/top")
def athlete_prs_top(athlete_id: int, limit: int = 5, session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    if current_user.id != athlete_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this athlete")
    return _pr_rows(session, athlete_id, limit=limit)


@router.get("/{athlete_id}/prs")
def athlete_prs(athlete_id: int, session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    if current_user.id != athlete_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this athlete")
    return _pr_rows(session, athlete_id, limit=None)


@router.get("/{athlete_id}/stats/overview")
def athlete_stats_overview(athlete_id: int, session: Session = Depends(get_session), current_user=Depends(get_current_user)):
    if current_user.id != athlete_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this athlete")
    return _overview_payload(session, athlete_id, top_limit=5)


def _clamp_capacity(value: float) -> float:
    try:
        return max(0.0, min(100.0, float(value)))
    except Exception:
        return 0.0
