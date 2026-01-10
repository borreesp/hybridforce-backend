import logging
from datetime import datetime, date
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

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
    PhysicalCapacityORM,
    WorkoutORM,
    WorkoutExecutionORM,
    UserSkillORM,
    MovementORM,
    WorkoutAnalysisORM,
)

router = APIRouter(dependencies=[Depends(get_current_user)])
logger = logging.getLogger("athlete.apply-impact")


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
    result_service = WorkoutResultService(session)
    created = result_service.create(
        WorkoutResultCreate(
            workout_id=workout_id,
            user_id=current_user.id,
            time_seconds=payload.time_seconds,
            difficulty=payload.difficulty,
            rating=payload.rating,
            comment=payload.comment,
        )
    )
    if not created:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User or workout not found")
    xp_service = WorkoutXPService(session)
    xp_awarded, snapshot = xp_service.award_for_result(
        current_user.id, workout_id, payload.time_seconds, payload.difficulty
    )
    achievement_service = AchievementService(session)
    unlocked = achievement_service.evaluate_level(current_user.id, snapshot["level"])
    mission_service = MissionService(session)
    completed, _ = mission_service.update_progress_for_workout(current_user.id, new_pr=False)
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
    mapping = {
        "resistance": "resistencia",
        "strength": "fuerza",
        "metcon": "metcon",
        "gymnastics": "gimnásticos",
        "speed": "velocidad",
    }
    return mapping.get(canonical.lower())


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
    candidates = {
        "skill_row": "Row",
        "skill_wall_balls": "Wall Ball",
        "skill_kettlebell_lunge": "Kettlebell Lunge",
        "skill_burpee_box_jump_over": "Burpee Box Jump Over",
    }
    mapping: Dict[str, int] = {}
    for key, name in candidates.items():
        mv = session.query(MovementORM).filter(func.lower(MovementORM.name) == name.lower()).first()
        if mv:
            mapping[key] = mv.id
    return mapping


@router.post("/workouts/{workout_analysis_id}/apply-impact")
def apply_workout_impact(
    workout_analysis_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """
    Aplica el impacto del WOD al perfil del atleta. Idempotente.
    """
    analysis_row: WorkoutAnalysisORM | None = (
        session.query(WorkoutAnalysisORM)
        .filter(WorkoutAnalysisORM.id == workout_analysis_id)
        .with_for_update()
        .first()
    )
    if not analysis_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout analysis not found")
    if analysis_row.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to apply this analysis")

    impact_delta = analysis_row.athlete_impact or {}
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
    cap_code_map = _capacity_code_map(session)
    skill_map = _skill_movement_map(session)
    applied_metrics: Dict[str, Any] = {}
    now = datetime.utcnow()

    for key, delta in impact_delta.items():
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
        new_value = base_value + delta
        applied_metrics[key] = new_value
        session.add(
            UserCapacityProfileORM(
                user_id=current_user.id,
                capacity_id=cap_id,
                value=int(round(new_value)),
                measured_at=now,
            )
        )

    tl_today = (
        session.query(UserTrainingLoadORM)
        .filter(UserTrainingLoadORM.user_id == current_user.id, UserTrainingLoadORM.load_date == date.today())
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
    delta_acute = float(impact_delta.get("acute_load", 0))
    delta_chronic = float(impact_delta.get("chronic_load", 0))
    delta_ratio = impact_delta.get("load_ratio")
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
            load_ratio=computed_ratio,
            notes=f"Impacto WOD {workout.id} analysis {analysis_id}",
        )
        session.add(tl_today)
    applied_metrics["acute_load"] = new_acute
    applied_metrics["chronic_load"] = new_chronic
    if computed_ratio is not None:
        applied_metrics["load_ratio"] = computed_ratio

    fatigue_delta = impact_delta.get("fatigue_score")
    if fatigue_delta is not None:
        latest_bio = (
            session.query(UserBiometricORM)
            .filter(UserBiometricORM.user_id == current_user.id)
            .order_by(UserBiometricORM.measured_at.desc())
            .first()
        )
        base_fatigue = float(latest_bio.fatigue_score) if latest_bio and latest_bio.fatigue_score is not None else 0.0
        new_fatigue = base_fatigue + float(fatigue_delta)
        session.add(
            UserBiometricORM(
                user_id=current_user.id,
                measured_at=now,
                fatigue_score=new_fatigue,
            )
        )
        applied_metrics["fatigue_score"] = new_fatigue

    for key, mv_id in skill_map.items():
        if key not in impact_delta:
            continue
        delta = impact_delta.get(key)
        if delta is None:
            continue
        latest_skill = (
            session.query(UserSkillORM)
            .filter(UserSkillORM.user_id == current_user.id, UserSkillORM.movement_id == mv_id)
            .order_by(UserSkillORM.measured_at.desc())
            .first()
        )
        base_score = float(latest_skill.skill_score) if latest_skill else 0.0
        new_score = base_score + float(delta)
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

    exec_row = WorkoutExecutionORM(
        workout_id=workout.id,
        user_id=current_user.id,
        executed_at=now,
        raw_ocr_json={"analysis_id": analysis_id, "impact_applied": True, "impact": impact_delta},
        notes=f"Impacto aplicado {now.isoformat()}",
    )
    session.add(exec_row)
    analysis_row.applied = True
    analysis_row.applied_at = now
    session.add(analysis_row)
    session.commit()

    logger.info(
        "[apply-impact] Applied impact for user=%s workout=%s metrics_updated=%s",
        current_user.id,
        workout.id,
        list(applied_metrics.keys()),
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

    return {"analysis": applied_analysis, "updated_profile": metrics, "impact": impact_delta}
