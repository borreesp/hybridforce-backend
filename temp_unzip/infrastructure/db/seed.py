from datetime import date, datetime, timedelta

from infrastructure.auth.security import hash_password
from infrastructure.db.models import (
    AchievementORM,
    AthleteLevelORM,
    EnergyDomainORM,
    EquipmentORM,
    EventORM,
    HyroxStationORM,
    IntensityLevelORM,
    MissionORM,
    MovementMuscleORM,
    MovementORM,
    MuscleGroupORM,
    PhysicalCapacityORM,
    TrainingPlanDayORM,
    TrainingPlanORM,
    UserAchievementORM,
    UserBiometricORM,
    UserCapacityProfileORM,
    UserEventORM,
    UserMissionORM,
    UserORM,
    UserPROM,
    UserProgressORM,
    UserSkillORM,
    UserTrainingLoadORM,
    WorkoutBlockMovementORM,
    WorkoutBlockORM,
    WorkoutCapacityORM,
    WorkoutEquipmentORM,
    WorkoutExecutionBlockORM,
    WorkoutExecutionORM,
    WorkoutHyroxStationORM,
    WorkoutLevelTimeORM,
    WorkoutMetadataORM,
    WorkoutMuscleORM,
    WorkoutORM,
    WorkoutStatsORM,
)


def _ensure_lookup(session, model, records):
    for rec in records:
        existing = session.query(model).filter_by(code=rec["code"]).first()
        if not existing:
            session.add(model(**rec))
    session.flush()


def _xp_levels():
    levels = []
    min_xp = 0
    for lvl in range(1, 51):
        span = int(round(200 * (lvl ** 1.35)))
        max_xp = min_xp + span
        levels.append(
            {
                "code": f"L{lvl}",
                "name": f"Nivel {lvl}",
                "description": f"Rango {min_xp}-{max_xp} XP",
                "sort_order": lvl,
                "min_xp": min_xp,
                "max_xp": max_xp,
            }
        )
        min_xp = max_xp
    return levels


def _seed_achievements(session):
    achievements = [
        {"code": "LEVEL_5", "name": "Nivel 5 alcanzado", "category": "progression", "xp_reward": 100},
        {"code": "LEVEL_10", "name": "Nivel 10 alcanzado", "category": "progression", "xp_reward": 200},
        {"code": "CONSISTENCY_WEEK", "name": "3 entrenos esta semana", "category": "consistency", "xp_reward": 120},
        {"code": "FIRST_PR", "name": "Primer PR registrado", "category": "pr", "xp_reward": 50},
        {"code": "HYROX_TRANSFER", "name": "Transfer HYROX alto", "category": "hyrox", "xp_reward": 150},
    ]
    for ach in achievements:
        if not session.query(AchievementORM).filter_by(code=ach["code"]).first():
            session.add(AchievementORM(**ach))
    session.flush()


def _seed_missions(session):
    missions = [
        {
            "type": "daily",
            "title": "Haz un WOD hoy",
            "description": "Completa cualquier entrenamiento en el dia",
            "xp_reward": 20,
            "condition_json": {"type": "wods", "target": 1, "window": "day"},
        },
        {
            "type": "weekly",
            "title": "Completa 3 entrenos esta semana",
            "description": "Consigue 3 sesiones registradas en 7 dias",
            "xp_reward": 100,
            "condition_json": {"type": "wods", "target": 3, "window": "week"},
        },
        {
            "type": "epic",
            "title": "Rompe un PR esta semana",
            "description": "Mejora cualquiera de tus marcas personales",
            "xp_reward": 300,
            "condition_json": {"type": "pr", "target": 1, "window": "week"},
        },
    ]
    for mission in missions:
        exists = (
            session.query(MissionORM)
            .filter(MissionORM.type == mission["type"], MissionORM.title == mission["title"])
            .first()
        )
        if not exists:
            session.add(MissionORM(**mission))
    session.flush()


def seed_data(session):
    athlete_levels = _xp_levels()
    intensity_levels = [
        {"code": "Baja", "name": "Baja", "sort_order": 1},
        {"code": "Media", "name": "Media", "sort_order": 2},
        {"code": "Alta", "name": "Alta", "sort_order": 3},
    ]
    energy_domains = [
        {"code": "AerÃ³bico", "name": "AerÃ³bico", "description": None},
        {"code": "AnaerÃ³bico", "name": "AnaerÃ³bico", "description": None},
        {"code": "Mixto", "name": "Mixto", "description": None},
    ]
    physical_capacities = [
        {"code": "Fuerza", "name": "Fuerza", "description": None},
        {"code": "Resistencia", "name": "Resistencia", "description": None},
        {"code": "Velocidad", "name": "Velocidad", "description": None},
        {"code": "Gimnásticos", "name": "Gimnásticos", "description": None},
        {"code": "Metcon", "name": "Metcon", "description": None},
        {"code": "Carga muscular", "name": "Carga muscular", "description": None},
    ]
    muscle_groups = [
        {"code": "Piernas", "name": "Piernas", "description": None},
        {"code": "Core", "name": "Core", "description": None},
        {"code": "Hombros", "name": "Hombros", "description": None},
        {"code": "Posterior", "name": "Posterior", "description": None},
        {"code": "Grip", "name": "Grip", "description": None},
        {"code": "Pecho", "name": "Pecho", "description": None},
        {"code": "Brazos", "name": "Brazos", "description": None},
    ]
    hyrox_stations = [
        {"code": "SkiErg", "name": "SkiErg", "description": None},
        {"code": "Sled Push", "name": "Sled Push", "description": None},
        {"code": "Sled Pull", "name": "Sled Pull", "description": None},
        {"code": "Farmers Carry", "name": "Farmers Carry", "description": None},
        {"code": "Burpee Broad Jump", "name": "Burpee Broad Jump", "description": None},
        {"code": "Row", "name": "Row", "description": None},
        {"code": "Sandbag Lunges", "name": "Sandbag Lunges", "description": None},
        {"code": "Wall Balls", "name": "Wall Balls", "description": None},
    ]

    _ensure_lookup(session, AthleteLevelORM, athlete_levels)
    _ensure_lookup(session, IntensityLevelORM, intensity_levels)
    _ensure_lookup(session, EnergyDomainORM, energy_domains)
    _ensure_lookup(session, PhysicalCapacityORM, physical_capacities)
    _ensure_lookup(session, MuscleGroupORM, muscle_groups)
    _ensure_lookup(session, HyroxStationORM, hyrox_stations)
    _seed_achievements(session)
    _seed_missions(session)

    if session.query(UserORM).count() > 0:
        session.commit()
        return

    def id_for(model, code):
        row = session.query(model).filter_by(code=code).first()
        return row.id if row else None

    # Movements base


        # Movements base
    run_mv = MovementORM(name="Run", category="Cardio", description="Running", default_load_unit=None)
    row_mv = MovementORM(name="Row", category="Cardio", description="Row erg", default_load_unit=None)
    wb_mv = MovementORM(name="Wall Ball", category="Metcon", description="Wall ball shot", default_load_unit="kg")
    dl_mv = MovementORM(name="Deadlift", category="Strength", description="Barbell deadlift", default_load_unit="kg")
    bbjo_mv = MovementORM(name="Burpee Box Jump Over", category="Metcon", description="BBJO", default_load_unit=None)
    kb_lunge_mv = MovementORM(name="Kettlebell Lunge", category="Metcon", description="KB lunge", default_load_unit="kg")

    # Movimientos extra para benchmarks CrossFit
    thruster_mv = MovementORM(
        name="Thruster",
        category="Metcon",
        description="Front squat into push press",
        default_load_unit="kg",
    )
    pullup_mv = MovementORM(
        name="Pull-up",
        category="Gimnásticos",
        description="Strict or kipping pull-up",
        default_load_unit=None,
    )
    pushup_mv = MovementORM(
        name="Push-up",
        category="Gimnásticos",
        description="Push-up al suelo",
        default_load_unit=None,
    )
    air_squat_mv = MovementORM(
        name="Air Squat",
        category="Gimnásticos",
        description="Sentadilla con peso corporal",
        default_load_unit=None,
    )
    box_jump_mv = MovementORM(
        name="Box Jump",
        category="Metcon",
        description="Salto al cajÃƒÂ³n",
        default_load_unit=None,
    )
    du_mv = MovementORM(
        name="Double Under",
        category="Metcon",
        description="Salto doble con comba",
        default_load_unit=None,
    )
    kb_swing_mv = MovementORM(
        name="KB Swing",
        category="Metcon",
        description="Kettlebell swing estilo americano o ruso",
        default_load_unit="kg",
    )
    situp_mv = MovementORM(
        name="Sit-up",
        category="Gimnásticos",
        description="Abdominal sit-up",
        default_load_unit=None,
    )

    session.add_all(
        [
            run_mv,
            row_mv,
            wb_mv,
            dl_mv,
            bbjo_mv,
            kb_lunge_mv,
            thruster_mv,
            pullup_mv,
            pushup_mv,
            air_squat_mv,
            box_jump_mv,
            du_mv,
            kb_swing_mv,
            situp_mv,
        ]
    )
    session.flush()

    def _shortened_metadata(**fields):
        limits = {
            "volume_total": 50,
            "work_rest_ratio": 20,
            "dominant_stimulus": 50,
            "load_type": 50,
            "session_load": 20,
        }
        for key, val in fields.items():
            if val is None:
                continue
            limit = limits.get(key)
            if limit and isinstance(val, str) and len(val) > limit:
                fields[key] = val[:limit]
        return fields

    def bind_muscle(mv, muscles):
        for m in muscles:
            session.add(
                MovementMuscleORM(
                    movement_id=mv.id,
                    muscle_group_id=id_for(MuscleGroupORM, m),
                    is_primary=True,
                )
            )

    # Binding de grupos musculares a movimientos
    bind_muscle(run_mv, ["Piernas"])
    bind_muscle(row_mv, ["Posterior", "Core"])
    bind_muscle(wb_mv, ["Piernas", "Hombros"])
    bind_muscle(dl_mv, ["Posterior", "Grip"])
    bind_muscle(bbjo_mv, ["Piernas", "Core"])
    bind_muscle(kb_lunge_mv, ["Piernas", "Core"])

    bind_muscle(thruster_mv, ["Piernas", "Hombros", "Core"])
    bind_muscle(pullup_mv, ["Posterior", "Brazos"])
    bind_muscle(pushup_mv, ["Pecho", "Brazos"])
    bind_muscle(air_squat_mv, ["Piernas"])
    bind_muscle(box_jump_mv, ["Piernas"])
    bind_muscle(du_mv, ["Piernas", "Grip"])
    bind_muscle(kb_swing_mv, ["Posterior", "Core", "Grip"])
    bind_muscle(situp_mv, ["Core"])

    # Usuario demo
    user_level_code = "L8"
    user = UserORM(
        name="Demo Athlete",
        email="demo@hybridforce.com",
        password=hash_password("changeme"),
        athlete_level_id=id_for(AthleteLevelORM, user_level_code),
    )
    session.add(user)
    session.flush()

    # User progress
    session.add(
        UserProgressORM(
            user_id=user.id,
            xp_total=8200,
            level=8,
            progress_pct=42,
        )
    )

    # Equipment
    rower = EquipmentORM(name="RowErg", description="Concept2 RowErg", price=899.00, category="Cardio")
    sled = EquipmentORM(name="Sled", description="Prowler sled", price=450.00, category="HYROX")
    kettlebell = EquipmentORM(name="Kettlebell", description="KB entreno", price=75.00, category="Metcon")
    rig = EquipmentORM(name="Pull-up Rig", description="Estructura para dominadas", price=1200.00, category="Gimnásticos")
    box = EquipmentORM(name="Plyo Box", description="CajÃƒÂ³n pliomÃƒÂ©trico", price=150.00, category="Metcon")
    barbell = EquipmentORM(name="Barbell", description="Barra olÃƒÂ­mpica", price=300.00, category="Strength")

    session.add_all([rower, sled, kettlebell, rig, box, barbell])
    session.flush()

    # =========================================
    # WODS HYROX + CROSSFIT (5 + 5) + base (3)
    # =========================================

    workouts = []

    # Helper shortcuts
    AERO = id_for(EnergyDomainORM, "Aerobico")
    ANA = id_for(EnergyDomainORM, "Anaerobico")
    MIX = id_for(EnergyDomainORM, "Mixto")

    LOW = id_for(IntensityLevelORM, "Baja")
    MID = id_for(IntensityLevelORM, "Media")
    HIGH = id_for(IntensityLevelORM, "Alta")

    MG_LEGS = id_for(MuscleGroupORM, "Piernas")
    MG_POST = id_for(MuscleGroupORM, "Posterior")
    MG_CORE = id_for(MuscleGroupORM, "Core")
    MG_SHOULDER = id_for(MuscleGroupORM, "Hombros")
    MG_CHEST = id_for(MuscleGroupORM, "Pecho")

    # -----------------------------------------
    # 3 WODs base ya existentes
    # -----------------------------------------
    engine = WorkoutORM(
        title="Engine Builder",
        description="10 rounds: 200m row + 10 wall balls. Rest 1:00",
        domain_id=AERO,
        intensity_level_id=MID,
        hyrox_transfer_level_id=MID,
        wod_type="Intervals",
        official_tag="HYROX friendly",
        main_muscle_group_id=MG_POST,
    )
    workouts.append(engine)

    hybrid = WorkoutORM(
        title="Hybrid Sprint",
        description="3 rounds for time: 800m run, 20 KB lunges, 15 BBJO",
        domain_id=MIX,
        intensity_level_id=HIGH,
        hyrox_transfer_level_id=HIGH,
        wod_type="Metcon",
        official_tag="Hybrid",
        main_muscle_group_id=MG_LEGS,
    )
    workouts.append(hybrid)

    strength = WorkoutORM(
        title="Strength Ladder",
        description="EMOM 12: Deadlift + Wall Balls",
        domain_id=ANA,
        intensity_level_id=MID,
        hyrox_transfer_level_id=MID,
        wod_type="Strength",
        official_tag="Gym",
        main_muscle_group_id=MG_POST,
    )
    workouts.append(strength)

    # -----------------------------------------
    # 5 HYROX WODs (orientados a carrera oficial)
    # -----------------------------------------

    hyrox_race = WorkoutORM(
        title="HYROX Race Sim Short",
        description=(
            "3 rounds for time: 1000m run + 500m row + 25 wall balls. "
            "Enfocado a simular el patrÃƒÂ³n carrera + estaciÃƒÂ³n."
        ),
        domain_id=MIX,
        intensity_level_id=HIGH,
        hyrox_transfer_level_id=HIGH,
        wod_type="Race Sim",
        official_tag="HYROX",
        main_muscle_group_id=MG_LEGS,
    )
    workouts.append(hyrox_race)

    hyrox_sled = WorkoutORM(
        title="HYROX Sled Engine",
        description="5 rounds: 400m run + 20 KB lunges (como sandbag lunges) + 10 BBJO",
        domain_id=MIX,
        intensity_level_id=HIGH,
        hyrox_transfer_level_id=HIGH,
        wod_type="Strength Endurance",
        official_tag="HYROX",
        main_muscle_group_id=MG_LEGS,
    )
    workouts.append(hyrox_sled)

    hyrox_wallballs = WorkoutORM(
        title="HYROX Wall Ball Benchmark",
        description="For time: 150 wall balls + 1000m row al final",
        domain_id=MIX,
        intensity_level_id=HIGH,
        hyrox_transfer_level_id=HIGH,
        wod_type="Benchmark",
        official_tag="HYROX",
        main_muscle_group_id=MG_LEGS,
    )
    workouts.append(hyrox_wallballs)

    hyrox_engine = WorkoutORM(
        title="HYROX Engine 4K",
        description="4 rounds: 800m run + 250m row + 10 KB lunges",
        domain_id=AERO,
        intensity_level_id=MID,
        hyrox_transfer_level_id=MID,
        wod_type="Engine",
        official_tag="HYROX",
        main_muscle_group_id=MG_LEGS,
    )
    workouts.append(hyrox_engine)

    hyrox_burpees = WorkoutORM(
        title="HYROX Burpee & Lunges",
        description="20 min AMRAP: 200m run + 10 BBJO + 20 KB lunges",
        domain_id=MIX,
        intensity_level_id=MID,
        hyrox_transfer_level_id=MID,
        wod_type="AMRAP",
        official_tag="HYROX",
        main_muscle_group_id=MG_LEGS,
    )
    workouts.append(hyrox_burpees)

    # -----------------------------------------
    # 5 CrossFit benchmark WODs oficiales
    # -----------------------------------------

    fran = WorkoutORM(
        title="Fran",
        description="21-15-9: Thrusters (42.5/30kg) + Pull-ups",
        domain_id=ANA,
        intensity_level_id=HIGH,
        hyrox_transfer_level_id=LOW,
        wod_type="Benchmark",
        official_tag="CrossFit",
        main_muscle_group_id=MG_LEGS,
    )
    workouts.append(fran)

    murph = WorkoutORM(
        title="Murph",
        description="1 mile run, 100 pull-ups, 200 push-ups, 300 air squats, 1 mile run (con o sin chaleco)",
        domain_id=AERO,
        intensity_level_id=HIGH,
        hyrox_transfer_level_id=MID,
        wod_type="Hero",
        official_tag="CrossFit",
        main_muscle_group_id=MG_LEGS,
    )
    workouts.append(murph)

    helen = WorkoutORM(
        title="Helen",
        description="3 rounds for time: 400m run, 21 KB swings, 12 pull-ups",
        domain_id=AERO,
        intensity_level_id=MID,
        hyrox_transfer_level_id=LOW,
        wod_type="Benchmark",
        official_tag="CrossFit",
        main_muscle_group_id=MG_LEGS,
    )
    workouts.append(helen)

    karen = WorkoutORM(
        title="Karen",
        description="For time: 150 wall balls",
        domain_id=ANA,
        intensity_level_id=MID,
        hyrox_transfer_level_id=HIGH,
        wod_type="Benchmark",
        official_tag="CrossFit",
        main_muscle_group_id=MG_LEGS,
    )
    workouts.append(karen)

    cindy = WorkoutORM(
        title="Cindy",
        description="20 min AMRAP: 5 pull-ups, 10 push-ups, 15 air squats",
        domain_id=ANA,
        intensity_level_id=LOW,
        hyrox_transfer_level_id=LOW,
        wod_type="AMRAP",
        official_tag="CrossFit",
        main_muscle_group_id=MG_LEGS,
    )
    workouts.append(cindy)

    session.add_all(workouts)
    session.flush()

    # =========================================
    # METADATA, STATS, CAPACITIES, LEVEL TIMES
    # =========================================

    # Engine Builder
    engine.metadata_rel = WorkoutMetadataORM(
        workout_id=engine.id,
        volume_total="2000m row + 100 wall balls",
        work_rest_ratio="1:1",
        dominant_stimulus="Cardio",
        load_type="Light",
        athlete_profile_desc="Atleta intermedio que necesita mejorar consistencia de ritmo y eficiencia en wall balls.",
        target_athlete_desc="HÃƒÂ­bridos que preparan HYROX o metcons largos.",
        pacing_tip="No salir fuerte; debe sentirse casi demasiado fÃƒÂ¡cil en las 3 primeras rondas.",
        pacing_detail="Mantener 70Ã¢â‚¬â€œ75% de esfuerzo las 5 primeras rondas y progresar al final.",
        break_tip="Micro-pauses de 2Ã¢â‚¬â€œ3 respiraciones entre sets de wall balls si sube el pulso.",
        rx_variant="Row a 1:50Ã¢â‚¬â€œ2:05/500m, balÃƒÂ³n 9/6kg.",
        scaled_variant="Row suave 2:10Ã¢â‚¬â€œ2:30/500m, 150m row + 8 WB con 6/4kg.",
        ai_observation="WOD perfecto para acumular metros sin un estrÃƒÂ©s brutal de sistema nervioso.",
        session_load="Moderate",
        session_feel="Pulso controlado, respiraciÃƒÂ³n continua.",
    )
    engine.stats = WorkoutStatsORM(
        workout_id=engine.id,
        estimated_difficulty=6.5,
        avg_time_seconds=1200,
        rating_count=0,
    )
    engine.level_times = [
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L1"), time_minutes=26.0, time_range="24-28"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L5"), time_minutes=22.0, time_range="21-23"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L10"), time_minutes=19.0, time_range="18-20"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L20"), time_minutes=17.0, time_range="16-18"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L30"), time_minutes=16.0, time_range="15-17"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L40"), time_minutes=15.0, time_range="14-16"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L50"), time_minutes=14.0, time_range="13-15"),
    ]
    engine.capacities = [
        WorkoutCapacityORM(
            capacity_id=id_for(PhysicalCapacityORM, "Resistencia"),
            value=80,
            note="Cardio continuo moderado.",
        ),
        WorkoutCapacityORM(
            capacity_id=id_for(PhysicalCapacityORM, "Carga muscular"),
            value=55,
            note="Carga acumulada en piernas y hombros.",
        ),
    ]
    engine.hyrox_stations = [
        WorkoutHyroxStationORM(station_id=id_for(HyroxStationORM, "Row"), transfer_pct=70),
        WorkoutHyroxStationORM(station_id=id_for(HyroxStationORM, "Wall Balls"), transfer_pct=60),
    ]
    engine.muscles = [
        WorkoutMuscleORM(muscle_group_id=MG_LEGS),
        WorkoutMuscleORM(muscle_group_id=MG_CORE),
        WorkoutMuscleORM(muscle_group_id=MG_SHOULDER),
    ]

    # Hybrid Sprint
    hybrid.metadata_rel = WorkoutMetadataORM(
        workout_id=hybrid.id,
        volume_total="2.4km run + 60 KB lunges + 45 BBJO",
        work_rest_ratio="4:1",
        dominant_stimulus="Mixto (cardio + metcon)",
        load_type="Bodyweight/KB",
        athlete_profile_desc="Atleta hÃƒÂ­brido con base aerÃƒÂ³bica decente y buena tolerancia a impacto.",
        target_athlete_desc="Intermedio/avanzado que compite en HYROX, OCR o functional fitness.",
        pacing_tip="Ronda 1 controlada, la sensaciÃƒÂ³n debe ser de reserva clara.",
        pacing_detail="Usar respiraciÃƒÂ³n nasal parcial en carrera para no reventar BBJO.",
        break_tip="Romper lunges 10/10 y BBJO en bloques de 5Ã¢â‚¬â€œ5Ã¢â‚¬â€œ5 si es necesario.",
        rx_variant="Run 800m / KB 24/16kg.",
        scaled_variant="Run 600m / KB 16/12kg / BBJO a box bajo.",
        ai_observation="Genera mucha fatiga de cadena posterior y cardio alto, ideal como test hÃƒÂ­brido.",
        session_load="High",
        session_feel="Fatiga global alta, especialmente piernas y pulmÃƒÂ³n.",
    )
    hybrid.stats = WorkoutStatsORM(
        workout_id=hybrid.id,
        estimated_difficulty=7.5,
        avg_time_seconds=1100,
        rating_count=0,
    )
    hybrid.level_times = [
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L1"), time_minutes=28.0, time_range="26-30"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L5"), time_minutes=24.0, time_range="23-25"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L10"), time_minutes=20.0, time_range="19-21"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L20"), time_minutes=18.0, time_range="17-19"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L30"), time_minutes=17.0, time_range="16-18"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L40"), time_minutes=16.0, time_range="15-17"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L50"), time_minutes=15.0, time_range="14-16"),
    ]
    hybrid.capacities = [
        WorkoutCapacityORM(
            capacity_id=id_for(PhysicalCapacityORM, "Resistencia"),
            value=78,
            note="Pacing en carrera.",
        ),
        WorkoutCapacityORM(
            capacity_id=id_for(PhysicalCapacityORM, "Metcon"),
            value=82,
            note="BBJO + lunges bajo fatiga.",
        ),
    ]
    hybrid.hyrox_stations = [
        WorkoutHyroxStationORM(station_id=id_for(HyroxStationORM, "Burpee Broad Jump"), transfer_pct=75),
        WorkoutHyroxStationORM(station_id=id_for(HyroxStationORM, "Sandbag Lunges"), transfer_pct=80),
        WorkoutHyroxStationORM(station_id=id_for(HyroxStationORM, "Row"), transfer_pct=60),
    ]
    hybrid.muscles = [
        WorkoutMuscleORM(muscle_group_id=MG_LEGS),
        WorkoutMuscleORM(muscle_group_id=MG_CORE),
    ]

    # Strength Ladder
    strength.metadata_rel = WorkoutMetadataORM(
        workout_id=strength.id,
        volume_total="EMOM 12 (DL + WB)",
        work_rest_ratio="1:1",
        dominant_stimulus="Fuerza-resistencia",
        load_type="Barbell + balon",
        athlete_profile_desc="Intermedio con tÃƒÂ©cnica correcta en DL y buena movilidad de hombro.",
        target_athlete_desc="Construir fuerza de base sin llegar al fallo.",
        pacing_tip="No escoger un peso que comprometa la lumbar.",
        pacing_detail="Dejar siempre 2Ã¢â‚¬â€œ3 reps en recÃƒÂ¡mara al final de cada minuto.",
        break_tip="Usar los ÃƒÂºltimos 10Ã¢â‚¬â€œ15s del minuto para respirar profundo.",
        rx_variant="DL 80/60kg + WB 9/6kg.",
        scaled_variant="DL 60/40kg + WB 6/4kg.",
        ai_observation="SesiÃƒÂ³n perfecta para trabajo de fuerza tÃƒÂ©cnica con toque metabÃƒÂ³lico.",
        session_load="Moderate",
        session_feel="Cansancio local en posterior y hombro.",
    )
    strength.stats = WorkoutStatsORM(
        workout_id=strength.id,
        estimated_difficulty=6.2,
        avg_time_seconds=900,
        rating_count=0,
    )
    strength.level_times = [
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L1"), time_minutes=16.0, time_range="15-17"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L5"), time_minutes=15.0, time_range="14-16"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L10"), time_minutes=14.0, time_range="13-15"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L20"), time_minutes=13.0, time_range="12-14"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L30"), time_minutes=12.5, time_range="12-13"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L40"), time_minutes=12.0, time_range="11-13"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L50"), time_minutes=11.5, time_range="11-12"),
    ]
    strength.capacities = [
        WorkoutCapacityORM(
            capacity_id=id_for(PhysicalCapacityORM, "Fuerza"),
            value=80,
            note="DL moderadamente pesado.",
        ),
        WorkoutCapacityORM(
            capacity_id=id_for(PhysicalCapacityORM, "Metcon"),
            value=60,
            note="WB bajo frecuencia cardiaca controlada.",
        ),
    ]
    strength.hyrox_stations = [
        WorkoutHyroxStationORM(station_id=id_for(HyroxStationORM, "Wall Balls"), transfer_pct=65),
    ]
    strength.muscles = [
        WorkoutMuscleORM(muscle_group_id=MG_POST),
        WorkoutMuscleORM(muscle_group_id=MG_SHOULDER),
    ]

    # ---------- HYROX WODs ----------

    hyrox_race.metadata_rel = WorkoutMetadataORM(
        workout_id=hyrox_race.id,
        volume_total="3km run + 1500m row + 75 wall balls",
        work_rest_ratio="Trabajo continuo",
        dominant_stimulus="Mixto (cardio + estaciones HYROX)",
        load_type="Bodyweight/mediana carga",
        athlete_profile_desc="Atleta que ya ha hecho o quiere hacer HYROX individual.",
        target_athlete_desc="Preparar sensaciÃƒÂ³n de 'race pace' pero en formato corto.",
        pacing_tip="Ritmo de carrera ligeramente mÃƒÂ¡s suave que ritmo de 1km en competiciÃƒÂ³n.",
        pacing_detail="Usar carrera para recuperar respiraciÃƒÂ³n y remar a ritmo estable.",
        break_tip="Wall balls en series de 15Ã¢â‚¬â€œ15Ã¢â‚¬â€œ10Ã¢â‚¬â€œ10Ã¢â‚¬â€œ10 con respiraciÃƒÂ³n controlada.",
        rx_variant="Run 1km / row moderado / WB 9/6kg.",
        scaled_variant="Run 800m / row 300m / WB 6/4kg (total 60 reps).",
        ai_observation="WOD perfecto para testear cÃƒÂ³mo se comporta el atleta con bloques largos de carrera + estaciÃƒÂ³n.",
        session_load="High",
        session_feel="SensaciÃƒÂ³n de mini carrera HYROX.",
    )
    hyrox_race.stats = WorkoutStatsORM(
        workout_id=hyrox_race.id,
        estimated_difficulty=7.8,
        avg_time_seconds=1800,
        rating_count=0,
    )
    hyrox_race.level_times = [
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L1"), time_minutes=40.0, time_range="38-42"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L5"), time_minutes=34.0, time_range="32-36"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L10"), time_minutes=30.0, time_range="28-32"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L20"), time_minutes=27.0, time_range="26-28"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L30"), time_minutes=25.0, time_range="24-26"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L40"), time_minutes=23.0, time_range="22-24"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L50"), time_minutes=21.0, time_range="20-22"),
    ]
    hyrox_race.capacities = [
        WorkoutCapacityORM(capacity_id=id_for(PhysicalCapacityORM, "Resistencia"), value=85, note="Cardio largo."),
        WorkoutCapacityORM(capacity_id=id_for(PhysicalCapacityORM, "Metcon"), value=70, note="WB bajo fatiga de carrera."),
        WorkoutCapacityORM(
            capacity_id=id_for(PhysicalCapacityORM, "Carga muscular"),
            value=65,
            note="Piernas acumuladas por km + WB.",
        ),
    ]
    hyrox_race.hyrox_stations = [
        WorkoutHyroxStationORM(station_id=id_for(HyroxStationORM, "Row"), transfer_pct=70),
        WorkoutHyroxStationORM(station_id=id_for(HyroxStationORM, "Wall Balls"), transfer_pct=80),
    ]
    hyrox_race.muscles = [
        WorkoutMuscleORM(muscle_group_id=MG_LEGS),
        WorkoutMuscleORM(muscle_group_id=MG_CORE),
    ]

    hyrox_sled.metadata_rel = WorkoutMetadataORM(
        workout_id=hyrox_sled.id,
        volume_total="2km run aprox + 100 lunges + 50 BBJO",
        work_rest_ratio="Intervalo denso",
        dominant_stimulus="Metcon pesado de piernas",
        load_type="KB/propio cuerpo",
        athlete_profile_desc="Atleta que sufre con sled push/pull y necesita mÃƒÂ¡s fuerza-resistencia de pierna.",
        target_athlete_desc="Mejorar tolerancia a lactato en piernas.",
        pacing_tip="Las dos primeras rondas deben sentirse mÃƒÂ¡s lentas de lo que te gustarÃƒÂ­a.",
        pacing_detail="Correr suave, lunges controlados y BBJO en bloques de 5.",
        break_tip="Respiraciones profundas al terminar lunges antes de empezar BBJO.",
        rx_variant="Run 400m / KB 24/16kg / BBJO estÃƒÂ¡ndar.",
        scaled_variant="Run 300m / KB 16/12kg / burpees normales.",
        ai_observation="Simula muy bien el patrÃƒÂ³n sensaciÃƒÂ³n de sled: piernas hinchadas y pulmÃƒÂ³n alto.",
        session_load="High",
        session_feel="Piernas ardiendo, respiraciÃƒÂ³n alta.",
    )
    hyrox_sled.stats = WorkoutStatsORM(
        workout_id=hyrox_sled.id,
        estimated_difficulty=8.0,
        avg_time_seconds=1500,
        rating_count=0,
    )
    hyrox_sled.level_times = [
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L1"), time_minutes=35.0, time_range="33-37"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L5"), time_minutes=30.0, time_range="28-32"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L10"), time_minutes=26.0, time_range="25-27"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L20"), time_minutes=23.0, time_range="22-24"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L30"), time_minutes=21.0, time_range="20-22"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L40"), time_minutes=19.0, time_range="18-20"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L50"), time_minutes=17.0, time_range="16-18"),
    ]
    hyrox_sled.capacities = [
        WorkoutCapacityORM(capacity_id=id_for(PhysicalCapacityORM, "Resistencia"), value=75, note="Cardio intervalado."),
        WorkoutCapacityORM(capacity_id=id_for(PhysicalCapacityORM, "Metcon"), value=85, note="Lunges + BBJO."),
        WorkoutCapacityORM(
            capacity_id=id_for(PhysicalCapacityORM, "Carga muscular"),
            value=80,
            note="Pierna muy cargada.",
        ),
    ]
    hyrox_sled.hyrox_stations = [
        WorkoutHyroxStationORM(station_id=id_for(HyroxStationORM, "Sandbag Lunges"), transfer_pct=85),
        WorkoutHyroxStationORM(station_id=id_for(HyroxStationORM, "Burpee Broad Jump"), transfer_pct=70),
    ]
    hyrox_sled.muscles = [
        WorkoutMuscleORM(muscle_group_id=MG_LEGS),
        WorkoutMuscleORM(muscle_group_id=MG_CORE),
    ]

    hyrox_wallballs.metadata_rel = WorkoutMetadataORM(
        workout_id=hyrox_wallballs.id,
        volume_total="150 wall balls + 1000m row",
        work_rest_ratio="Block unico",
        dominant_stimulus="Carga muscular de piernas y hombro",
        load_type="BalÃƒÂ³n + erg",
        athlete_profile_desc="Cualquier atleta HYROX que quiera testear su estaciÃƒÂ³n final.",
        target_athlete_desc="Practicar pacing y breaks ÃƒÂ³ptimos en wall balls.",
        pacing_tip="Nunca ir a fallo; series cortas y constantes.",
        pacing_detail="Por ejemplo 15Ãƒâ€”10 reps con pausa breve entre series.",
        break_tip="Fijar nÃƒÂºmero de respiraciones entre sets (3Ã¢â‚¬â€œ5).",
        rx_variant="WB 9/6kg, objetivo a altura estÃƒÂ¡ndar HYROX.",
        scaled_variant="WB 6/4kg con total 100 reps + 800m row.",
        ai_observation="Excelente benchmark especÃƒÂ­fico para ver cÃƒÂ³mo llegas a la ÃƒÂºltima estaciÃƒÂ³n de la race.",
        session_load="High",
        session_feel="Piernas y hombros muy cargados, cardio medio-alto.",
    )
    hyrox_wallballs.stats = WorkoutStatsORM(
        workout_id=hyrox_wallballs.id,
        estimated_difficulty=7.2,
        avg_time_seconds=1200,
        rating_count=0,
    )
    hyrox_wallballs.level_times = [
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L1"), time_minutes=30.0, time_range="28-32"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L5"), time_minutes=24.0, time_range="23-25"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L10"), time_minutes=20.0, time_range="19-21"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L20"), time_minutes=18.0, time_range="17-19"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L30"), time_minutes=16.0, time_range="15-17"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L40"), time_minutes=15.0, time_range="14-16"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L50"), time_minutes=14.0, time_range="13-15"),
    ]
    hyrox_wallballs.capacities = [
        WorkoutCapacityORM(
            capacity_id=id_for(PhysicalCapacityORM, "Carga muscular"),
            value=90,
            note="Pierna/cuÃƒÂ¡driceps al lÃƒÂ­mite.",
        ),
        WorkoutCapacityORM(
            capacity_id=id_for(PhysicalCapacityORM, "Metcon"),
            value=75,
            note="Cardio medio-alto por densidad de reps.",
        ),
    ]
    hyrox_wallballs.hyrox_stations = [
        WorkoutHyroxStationORM(station_id=id_for(HyroxStationORM, "Wall Balls"), transfer_pct=95),
        WorkoutHyroxStationORM(station_id=id_for(HyroxStationORM, "Row"), transfer_pct=50),
    ]
    hyrox_wallballs.muscles = [
        WorkoutMuscleORM(muscle_group_id=MG_LEGS),
        WorkoutMuscleORM(muscle_group_id=MG_SHOULDER),
        WorkoutMuscleORM(muscle_group_id=MG_CORE),
    ]

    hyrox_engine.metadata_rel = WorkoutMetadataORM(
        workout_id=hyrox_engine.id,
        volume_total="3.2km run + 1km row + 40 KB lunges",
        work_rest_ratio="Bloques largos",
        dominant_stimulus="Engine aerÃƒÂ³bico",
        load_type="Cardio + KB ligera",
        athlete_profile_desc="Atleta que respira bien pero le falta tiempo bajo tensiÃƒÂ³n en carrera.",
        target_athlete_desc="Construir base aerÃƒÂ³bica especÃƒÂ­fica para HYROX.",
        pacing_tip="Ritmo de carrera conversacional (70%).",
        pacing_detail="Usar row como 'descanso activo' para bajar un poco pulsaciones.",
        break_tip="Romper lunges en series de 10 con pausa corta.",
        rx_variant="Run 800m / row 250m / KB 24/16kg.",
        scaled_variant="Run 600m / row 200m / KB 16/12kg.",
        ai_observation="SesiÃƒÂ³n muy ÃƒÂºtil para dÃƒÂ­as donde quieres acumular volumen pero sin destrozarte.",
        session_load="Moderate",
        session_feel="SensaciÃƒÂ³n de 'largo controlado'.",
    )
    hyrox_engine.stats = WorkoutStatsORM(
        workout_id=hyrox_engine.id,
        estimated_difficulty=6.8,
        avg_time_seconds=2100,
        rating_count=0,
    )
    hyrox_engine.level_times = [
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L1"), time_minutes=45.0, time_range="43-47"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L5"), time_minutes=38.0, time_range="36-40"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L10"), time_minutes=34.0, time_range="32-36"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L20"), time_minutes=30.0, time_range="29-31"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L30"), time_minutes=28.0, time_range="27-29"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L40"), time_minutes=26.0, time_range="25-27"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L50"), time_minutes=24.0, time_range="23-25"),
    ]
    hyrox_engine.capacities = [
        WorkoutCapacityORM(capacity_id=id_for(PhysicalCapacityORM, "Resistencia"), value=88, note="Engine puro."),
        WorkoutCapacityORM(
            capacity_id=id_for(PhysicalCapacityORM, "Carga muscular"),
            value=60,
            note="Pierna moderadamente cargada por lunges.",
        ),
    ]
    hyrox_engine.hyrox_stations = [
        WorkoutHyroxStationORM(station_id=id_for(HyroxStationORM, "Row"), transfer_pct=65),
        WorkoutHyroxStationORM(station_id=id_for(HyroxStationORM, "Sandbag Lunges"), transfer_pct=70),
    ]
    hyrox_engine.muscles = [
        WorkoutMuscleORM(muscle_group_id=MG_LEGS),
        WorkoutMuscleORM(muscle_group_id=MG_CORE),
    ]

    hyrox_burpees.metadata_rel = WorkoutMetadataORM(
        workout_id=hyrox_burpees.id,
        volume_total="Muchos burpees + lunges + carrera corta",
        work_rest_ratio="AMRAP denso",
        dominant_stimulus="Metcon + tolerancia a impacto",
        load_type="Bodyweight/KB ligera",
        athlete_profile_desc="Atletas que sufren las estaciones de burpee broad jump y lunges.",
        target_athlete_desc="Mejorar resiliencia mental bajo fatiga.",
        pacing_tip="Desde el minuto 1 como si fuera el minuto 15.",
        pacing_detail="Buscar ritmo sostenible de burpees que no se dispare a rojo.",
        break_tip="Parar de pie 3 respiraciones entre sets, nunca desplomado en el suelo.",
        rx_variant="BBJO estÃƒÂ¡ndar + KB 24/16kg.",
        scaled_variant="Burpees sencillos + KB 16/12kg.",
        ai_observation="Muy buen test mental y de consistencia de movimiento.",
        session_load="High",
        session_feel="Fatiga respiratoria marcada.",
    )
    hyrox_burpees.stats = WorkoutStatsORM(
        workout_id=hyrox_burpees.id,
        estimated_difficulty=7.4,
        avg_time_seconds=1200,
        rating_count=0,
    )
    hyrox_burpees.level_times = [
        # aquÃƒÂ­ el tiempo es duraciÃƒÂ³n fija (20'), pero usamos referencia
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L1"), time_minutes=20.0, time_range="20-20"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L5"), time_minutes=20.0, time_range="20-20"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L10"), time_minutes=20.0, time_range="20-20"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L20"), time_minutes=20.0, time_range="20-20"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L30"), time_minutes=20.0, time_range="20-20"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L40"), time_minutes=20.0, time_range="20-20"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L50"), time_minutes=20.0, time_range="20-20"),
    ]
    hyrox_burpees.capacities = [
        WorkoutCapacityORM(capacity_id=id_for(PhysicalCapacityORM, "Metcon"), value=90, note="Burpees + lunges."),
        WorkoutCapacityORM(
            capacity_id=id_for(PhysicalCapacityORM, "Resistencia"),
            value=70,
            note="Sostener durante 20 minutos.",
        ),
    ]
    hyrox_burpees.hyrox_stations = [
        WorkoutHyroxStationORM(station_id=id_for(HyroxStationORM, "Burpee Broad Jump"), transfer_pct=85),
        WorkoutHyroxStationORM(station_id=id_for(HyroxStationORM, "Sandbag Lunges"), transfer_pct=75),
    ]
    hyrox_burpees.muscles = [
        WorkoutMuscleORM(muscle_group_id=MG_LEGS),
        WorkoutMuscleORM(muscle_group_id=MG_CORE),
    ]

    # ---------- CROSSFIT BENCHMARKS ----------

    fran.metadata_rel = WorkoutMetadataORM(
        workout_id=fran.id,
        volume_total="45 thrusters + 45 pull-ups",
        work_rest_ratio="Sprint total",
        dominant_stimulus="Metcon muy agresivo",
        load_type="Barbell + gimnÃƒÂ¡sticos",
        athlete_profile_desc="Atleta con buena tÃƒÂ©cnica en thruster y kipping/chest-to-bar.",
        target_athlete_desc="Test clÃƒÂ¡sico de potencia anaerÃƒÂ³bica.",
        pacing_tip="Si tardas mÃƒÂ¡s de 7', no es un sprint, es un broken benchmark.",
        pacing_detail="Atletas avanzados: 21 unbroken o 12/9; resto 9/6/6 o similar.",
        break_tip="Descansos muy cortos, 3Ã¢â‚¬â€œ5 respiraciones, siempre de pie.",
        rx_variant="Thruster 42.5/30kg, pull-ups Rx.",
        scaled_variant="Thruster 30/20kg + jumping pull-ups o ring rows.",
        ai_observation="WOD perfecto para evaluar engine anaerÃƒÂ³bico y habilidad gimnÃƒÂ¡stica.",
        session_load="High",
        session_feel="Lactato mÃƒÂ¡ximo, sensaciÃƒÂ³n de ahogo breve.",
    )
    fran.stats = WorkoutStatsORM(
        workout_id=fran.id,
        estimated_difficulty=8.5,
        avg_time_seconds=360,
        rating_count=0,
    )
    fran.level_times = [
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L1"), time_minutes=10.0, time_range="9-11"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L5"), time_minutes=7.0, time_range="6-8"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L10"), time_minutes=5.5, time_range="5-6"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L20"), time_minutes=4.5, time_range="4-5"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L30"), time_minutes=4.0, time_range="3-4"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L40"), time_minutes=3.5, time_range="3-4"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L50"), time_minutes=3.0, time_range="2-3"),
    ]
    fran.capacities = [
        WorkoutCapacityORM(capacity_id=id_for(PhysicalCapacityORM, "Metcon"), value=95, note="Sprint brutal."),
        WorkoutCapacityORM(
            capacity_id=id_for(PhysicalCapacityORM, "Gimnásticos"),
            value=80,
            note="Pull-ups bajo estrÃƒÂ©s.",
        ),
        WorkoutCapacityORM(
            capacity_id=id_for(PhysicalCapacityORM, "Carga muscular"),
            value=75,
            note="Hombros y cuÃƒÂ¡driceps muy cargados.",
        ),
    ]
    fran.muscles = [
        WorkoutMuscleORM(muscle_group_id=MG_LEGS),
        WorkoutMuscleORM(muscle_group_id=MG_SHOULDER),
        WorkoutMuscleORM(muscle_group_id=MG_CORE),
    ]

    murph.metadata_rel = WorkoutMetadataORM(
        workout_id=murph.id,
        volume_total="2 miles run + 100 pull-ups + 200 push-ups + 300 squats",
        work_rest_ratio="Endurance hero",
        dominant_stimulus="Resistencia larga + carga muscular brutal",
        load_type="Bodyweight (con o sin chaleco)",
        athlete_profile_desc="Atleta con experiencia y respeto por el volumen.",
        target_athlete_desc="Test mental y fÃƒÂ­sico anual.",
        pacing_tip="Particionar desde el principio: nunca 'ir a por ello' de primeras.",
        pacing_detail="ClÃƒÂ¡sico: 20 rondas de 5/10/15 con ritmo constante.",
        break_tip="Si usas chaleco, sÃƒÂ© conservador y prioriza tÃƒÂ©cnica limpia.",
        rx_variant="Con chaleco 9/6kg.",
        scaled_variant="Sin chaleco + volumen reducido (por ejemplo 75/150/225).",
        ai_observation="No es un WOD para hacer cada semana; pensarlo como evento.",
        session_load="Very High",
        session_feel="Extremadamente demandante, fatiga residual varios dÃƒÂ­as.",
    )
    murph.stats = WorkoutStatsORM(
        workout_id=murph.id,
        estimated_difficulty=9.5,
        avg_time_seconds=3000,
        rating_count=0,
    )
    murph.level_times = [
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L1"), time_minutes=80.0, time_range="75-90"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L5"), time_minutes=65.0, time_range="60-70"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L10"), time_minutes=55.0, time_range="50-60"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L20"), time_minutes=48.0, time_range="45-50"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L30"), time_minutes=42.0, time_range="40-45"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L40"), time_minutes=38.0, time_range="36-40"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L50"), time_minutes=35.0, time_range="32-36"),
    ]
    murph.capacities = [
        WorkoutCapacityORM(capacity_id=id_for(PhysicalCapacityORM, "Resistencia"), value=95, note="Endurance extremo."),
        WorkoutCapacityORM(
            capacity_id=id_for(PhysicalCapacityORM, "Gimnásticos"),
            value=85,
            note="Volumen de tracciÃƒÂ³n y empuje enorme.",
        ),
        WorkoutCapacityORM(
            capacity_id=id_for(PhysicalCapacityORM, "Carga muscular"),
            value=95,
            note="Piernas destrozadas por air squats.",
        ),
    ]
    murph.muscles = [
        WorkoutMuscleORM(muscle_group_id=MG_LEGS),
        WorkoutMuscleORM(muscle_group_id=MG_CHEST),
        WorkoutMuscleORM(muscle_group_id=MG_CORE),
    ]

    helen.metadata_rel = WorkoutMetadataORM(
        workout_id=helen.id,
        volume_total="1.2km run + 63 KB swings + 36 pull-ups",
        work_rest_ratio="Metcon 3 rondas",
        dominant_stimulus="Resistencia + gimnÃƒÂ¡sticos ligeros",
        load_type="KB + peso corporal",
        athlete_profile_desc="Atleta con tÃƒÂ©cnica decente de swing y pull-up.",
        target_athlete_desc="Buen benchmark mixto sin ser mortal.",
        pacing_tip="Ritmo de carrera estable, swings unbroken si es posible.",
        pacing_detail="Pull-ups en 2Ã¢â‚¬â€œ3 sets dependiendo del nivel.",
        break_tip="No correr tan rÃƒÂ¡pido que luego 'mueras' en la barra.",
        rx_variant="KB 24/16kg.",
        scaled_variant="KB 16/12kg + jumping pull-ups.",
        ai_observation="Ideal como referencia de cÃƒÂ³mo se comporta el engine medio del atleta.",
        session_load="Moderate",
        session_feel="Llega cansado pero recupera rÃƒÂ¡pido.",
    )
    helen.stats = WorkoutStatsORM(
        workout_id=helen.id,
        estimated_difficulty=7.0,
        avg_time_seconds=720,
        rating_count=0,
    )
    helen.level_times = [
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L1"), time_minutes=18.0, time_range="17-19"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L5"), time_minutes=15.0, time_range="14-16"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L10"), time_minutes=13.0, time_range="12-14"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L20"), time_minutes=11.5, time_range="11-12"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L30"), time_minutes=10.5, time_range="10-11"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L40"), time_minutes=9.5, time_range="9-10"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L50"), time_minutes=8.5, time_range="8-9"),
    ]
    helen.capacities = [
        WorkoutCapacityORM(capacity_id=id_for(PhysicalCapacityORM, "Resistencia"), value=80, note="Carrera."),
        WorkoutCapacityORM(capacity_id=id_for(PhysicalCapacityORM, "Metcon"), value=75, note="Mezcla con swings."),
        WorkoutCapacityORM(
            capacity_id=id_for(PhysicalCapacityORM, "Gimnásticos"),
            value=70,
            note="Pull-ups a ritmo moderado.",
        ),
    ]
    helen.muscles = [
        WorkoutMuscleORM(muscle_group_id=MG_LEGS),
        WorkoutMuscleORM(muscle_group_id=MG_POST),
        WorkoutMuscleORM(muscle_group_id=MG_CORE),
    ]

    karen.metadata_rel = WorkoutMetadataORM(
        workout_id=karen.id,
        volume_total="150 wall balls",
        work_rest_ratio="Block unico",
        dominant_stimulus="Carga muscular de pierna y hombro",
        load_type="BalÃƒÂ³n",
        athlete_profile_desc="Atleta con buena mecÃƒÂ¡nica de sentadilla frontal y movilidad suficiente.",
        target_athlete_desc="Ver tolerancia a volumen de WB.",
        pacing_tip="Nunca ir a fallo; siempre dejar 3Ã¢â‚¬â€œ5 reps 'dentro'.",
        pacing_detail="Dividir en bloques pequeÃƒÂ±os (por ejemplo 15Ãƒâ€”10 o 10Ãƒâ€”15).",
        break_tip="Pausas activas de 5 respiraciones mirando al balÃƒÂ³n.",
        rx_variant="WB 9/6kg.",
        scaled_variant="WB 6/4kg y total 90Ã¢â‚¬â€œ120 reps.",
        ai_observation="Muy transferible a HYROX (estaciÃƒÂ³n 8).",
        session_load="Moderate-High",
        session_feel="Piernas tocadas, respiraciÃƒÂ³n alta pero no extremo.",
    )
    karen.stats = WorkoutStatsORM(
        workout_id=karen.id,
        estimated_difficulty=7.0,
        avg_time_seconds=900,
        rating_count=0,
    )
    karen.level_times = [
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L1"), time_minutes=20.0, time_range="18-22"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L5"), time_minutes=16.0, time_range="15-17"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L10"), time_minutes=13.0, time_range="12-14"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L20"), time_minutes=11.0, time_range="10-12"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L30"), time_minutes=10.0, time_range="9-11"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L40"), time_minutes=9.0, time_range="8-10"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L50"), time_minutes=8.0, time_range="7-9"),
    ]
    karen.capacities = [
        WorkoutCapacityORM(
            capacity_id=id_for(PhysicalCapacityORM, "Carga muscular"),
            value=88,
            note="Piernas + hombros.",
        ),
        WorkoutCapacityORM(
            capacity_id=id_for(PhysicalCapacityORM, "Metcon"),
            value=70,
            note="Cardio sostenido por densidad de reps.",
        ),
    ]
    karen.muscles = [
        WorkoutMuscleORM(muscle_group_id=MG_LEGS),
        WorkoutMuscleORM(muscle_group_id=MG_SHOULDER),
        WorkoutMuscleORM(muscle_group_id=MG_CORE),
    ]

    cindy.metadata_rel = WorkoutMetadataORM(
        workout_id=cindy.id,
        volume_total="AMRAP 20 de 5/10/15",
        work_rest_ratio="Trabajo continuo",
        dominant_stimulus="GimnÃƒÂ¡sticos + resistencia",
        load_type="Peso corporal",
        athlete_profile_desc="Atleta con base gimnÃƒÂ¡stica decente.",
        target_athlete_desc="Construir volumen a RPE medio.",
        pacing_tip="Desde el minuto 1 como si estuvieras en el 15.",
        pacing_detail="Mejor 18 rondas constantes que 10 rÃƒÂ¡pidas y morir.",
        break_tip="Evitar llegar al fallo en push-ups; partir desde el inicio.",
        rx_variant="Pull-ups Rx.",
        scaled_variant="Ring rows + knee push-ups.",
        ai_observation="Muy buen WOD para ver 'bodyweight engine'.",
        session_load="Moderate",
        session_feel="Cansancio acumulado pero manejable.",
    )
    cindy.stats = WorkoutStatsORM(
        workout_id=cindy.id,
        estimated_difficulty=6.5,
        avg_time_seconds=1200,
        rating_count=0,
    )
    cindy.level_times = [
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L1"), time_minutes=20.0, time_range="20-20"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L5"), time_minutes=20.0, time_range="20-20"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L10"), time_minutes=20.0, time_range="20-20"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L20"), time_minutes=20.0, time_range="20-20"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L30"), time_minutes=20.0, time_range="20-20"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L40"), time_minutes=20.0, time_range="20-20"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "L50"), time_minutes=20.0, time_range="20-20"),
    ]
    cindy.capacities = [
        WorkoutCapacityORM(capacity_id=id_for(PhysicalCapacityORM, "Gimnásticos"), value=80, note="Volumen bodyweight."),
        WorkoutCapacityORM(
            capacity_id=id_for(PhysicalCapacityORM, "Resistencia"),
            value=70,
            note="20' sostenidos.",
        ),
    ]
    cindy.muscles = [
        WorkoutMuscleORM(muscle_group_id=MG_LEGS),
        WorkoutMuscleORM(muscle_group_id=MG_CHEST),
        WorkoutMuscleORM(muscle_group_id=MG_CORE),
    ]

    session.flush()

    # =========================================
    # BLOQUES Y MOVIMIENTOS POR WOD
    # =========================================

    def build_block(workout, position, block_type, title, description, rounds=None, duration_seconds=None, notes=None):
        blk = WorkoutBlockORM(
            workout_id=workout.id,
            position=position,
            block_type=block_type,
            title=title,
            description=description,
            rounds=rounds,
            duration_seconds=duration_seconds,
            notes=notes,
        )
        session.add(blk)
        session.flush()
        return blk

    # Engine blocks
    eng_warm = build_block(engine, 1, "warmup", "Calentamiento", "Row easy pace 5-8 minutos")
    eng_main = build_block(
        engine,
        2,
        "intervals",
        "10 rounds",
        "200m row + 10 wall balls, rest 1:00",
        rounds=10,
    )
    session.add_all(
        [
            WorkoutBlockMovementORM(
                workout_block_id=eng_main.id,
                movement_id=row_mv.id,
                position=1,
                distance_meters=200,
            ),
            WorkoutBlockMovementORM(
                workout_block_id=eng_main.id,
                movement_id=wb_mv.id,
                position=2,
                reps=10,
                load=9,
                load_unit="kg",
            ),
        ]
    )

    # Hybrid blocks
    hyb_warm = build_block(
        hybrid,
        1,
        "warmup",
        "Calentamiento",
        "Movilidad de cadera + trote suave 5'",
    )
    hyb_block = build_block(
        hybrid,
        2,
        "for_time",
        "3 rounds",
        "800m run + 20 KB lunges + 15 BBJO",
        rounds=3,
    )
    session.add_all(
        [
            WorkoutBlockMovementORM(
                workout_block_id=hyb_block.id,
                movement_id=run_mv.id,
                position=1,
                distance_meters=800,
            ),
            WorkoutBlockMovementORM(
                workout_block_id=hyb_block.id,
                movement_id=kb_lunge_mv.id,
                position=2,
                reps=20,
                load=24,
                load_unit="kg",
            ),
            WorkoutBlockMovementORM(
                workout_block_id=hyb_block.id,
                movement_id=bbjo_mv.id,
                position=3,
                reps=15,
            ),
        ]
    )

    # Strength blocks
    str_warm = build_block(
        strength,
        1,
        "warmup",
        "Calentamiento especÃƒÂ­fico",
        "Series progresivas de DL ligeros + wall balls suaves",
    )
    str_block = build_block(
        strength,
        2,
        "emom",
        "EMOM 12",
        "Cada minuto: Deadlift + Wall Balls",
        rounds=12,
    )
    session.add_all(
        [
            WorkoutBlockMovementORM(
                workout_block_id=str_block.id,
                movement_id=dl_mv.id,
                position=1,
                reps=8,
                load=80,
                load_unit="kg",
            ),
            WorkoutBlockMovementORM(
                workout_block_id=str_block.id,
                movement_id=wb_mv.id,
                position=2,
                reps=12,
                load=9,
                load_unit="kg",
            ),
        ]
    )

    # HYROX Race Sim Short blocks
    hr_warm = build_block(
        hyrox_race,
        1,
        "warmup",
        "Calentamiento HYROX",
        "5' run suave + movilidad de tobillo y cadera",
    )
    hr_main = build_block(
        hyrox_race,
        2,
        "for_time",
        "3 rounds HYROX Short",
        "1000m run + 500m row + 25 wall balls",
        rounds=3,
    )
    session.add_all(
        [
            WorkoutBlockMovementORM(
                workout_block_id=hr_main.id,
                movement_id=run_mv.id,
                position=1,
                distance_meters=1000,
            ),
            WorkoutBlockMovementORM(
                workout_block_id=hr_main.id,
                movement_id=row_mv.id,
                position=2,
                distance_meters=500,
            ),
            WorkoutBlockMovementORM(
                workout_block_id=hr_main.id,
                movement_id=wb_mv.id,
                position=3,
                reps=25,
                load=9,
                load_unit="kg",
            ),
        ]
    )

    # HYROX Sled Engine blocks
    hs_warm = build_block(
        hyrox_sled,
        1,
        "warmup",
        "Activation legs",
        "Saltos suaves, lunges sin peso, movilidad.",
    )
    hs_main = build_block(
        hyrox_sled,
        2,
        "for_time",
        "5 rounds",
        "400m run + 20 KB lunges + 10 BBJO",
        rounds=5,
    )
    session.add_all(
        [
            WorkoutBlockMovementORM(
                workout_block_id=hs_main.id,
                movement_id=run_mv.id,
                position=1,
                distance_meters=400,
            ),
            WorkoutBlockMovementORM(
                workout_block_id=hs_main.id,
                movement_id=kb_lunge_mv.id,
                position=2,
                reps=20,
                load=24,
                load_unit="kg",
            ),
            WorkoutBlockMovementORM(
                workout_block_id=hs_main.id,
                movement_id=bbjo_mv.id,
                position=3,
                reps=10,
            ),
        ]
    )

    # HYROX Wall Ball Benchmark blocks
    hwb_warm = build_block(
        hyrox_wallballs,
        1,
        "warmup",
        "Mobility + patterning",
        "Wall balls ligeros + sentadillas.",
    )
    hwb_main = build_block(
        hyrox_wallballs,
        2,
        "for_time",
        "Benchmark Wall Balls",
        "150 wall balls + 1000m row",
    )
    session.add_all(
        [
            WorkoutBlockMovementORM(
                workout_block_id=hwb_main.id,
                movement_id=wb_mv.id,
                position=1,
                reps=150,
                load=9,
                load_unit="kg",
            ),
            WorkoutBlockMovementORM(
                workout_block_id=hwb_main.id,
                movement_id=row_mv.id,
                position=2,
                distance_meters=1000,
            ),
        ]
    )

    # HYROX Engine 4K blocks
    he_warm = build_block(
        hyrox_engine,
        1,
        "warmup",
        "Run + row easy",
        "5' trote + 3' row suave.",
    )
    he_main = build_block(
        hyrox_engine,
        2,
        "for_time",
        "4 rounds",
        "800m run + 250m row + 10 KB lunges",
        rounds=4,
    )
    session.add_all(
        [
            WorkoutBlockMovementORM(
                workout_block_id=he_main.id,
                movement_id=run_mv.id,
                position=1,
                distance_meters=800,
            ),
            WorkoutBlockMovementORM(
                workout_block_id=he_main.id,
                movement_id=row_mv.id,
                position=2,
                distance_meters=250,
            ),
            WorkoutBlockMovementORM(
                workout_block_id=he_main.id,
                movement_id=kb_lunge_mv.id,
                position=3,
                reps=10,
                load=24,
                load_unit="kg",
            ),
        ]
    )

    # HYROX Burpee & Lunges blocks
    hb_warm = build_block(
        hyrox_burpees,
        1,
        "warmup",
        "General warmup",
        "Run suave 5' + movilidad.",
    )
    hb_main = build_block(
        hyrox_burpees,
        2,
        "amrap",
        "AMRAP 20",
        "200m run + 10 BBJO + 20 KB lunges",
        duration_seconds=20 * 60,
    )
    session.add_all(
        [
            WorkoutBlockMovementORM(
                workout_block_id=hb_main.id,
                movement_id=run_mv.id,
                position=1,
                distance_meters=200,
            ),
            WorkoutBlockMovementORM(
                workout_block_id=hb_main.id,
                movement_id=bbjo_mv.id,
                position=2,
                reps=10,
            ),
            WorkoutBlockMovementORM(
                workout_block_id=hb_main.id,
                movement_id=kb_lunge_mv.id,
                position=3,
                reps=20,
                load=24,
                load_unit="kg",
            ),
        ]
    )

    # Fran blocks
    fr_warm = build_block(
        fran,
        1,
        "warmup",
        "Warm-up Fran",
        "Movilidad hombro + thrusters ligeros + swings/pull-ups fÃƒÂ¡ciles.",
    )
    fr_main = build_block(
        fran,
        2,
        "for_time",
        "Fran original",
        "21-15-9 Thrusters + Pull-ups",
    )
    session.add_all(
        [
            WorkoutBlockMovementORM(
                workout_block_id=fr_main.id,
                movement_id=thruster_mv.id,
                position=1,
                reps=45,
                load=42.5,
                load_unit="kg",
            ),
            WorkoutBlockMovementORM(
                workout_block_id=fr_main.id,
                movement_id=pullup_mv.id,
                position=2,
                reps=45,
            ),
        ]
    )

    # Murph blocks
    mu_warm = build_block(
        murph,
        1,
        "warmup",
        "Pre-Murph",
        "Run suave + movilidad hombro/cadera.",
    )
    mu_main = build_block(
        murph,
        2,
        "for_time",
        "Murph",
        "1 mile run, 100 pull-ups, 200 push-ups, 300 air squats, 1 mile run",
    )
    session.add_all(
        [
            WorkoutBlockMovementORM(
                workout_block_id=mu_main.id,
                movement_id=run_mv.id,
                position=1,
                distance_meters=1609,
            ),
            WorkoutBlockMovementORM(
                workout_block_id=mu_main.id,
                movement_id=pullup_mv.id,
                position=2,
                reps=100,
            ),
            WorkoutBlockMovementORM(
                workout_block_id=mu_main.id,
                movement_id=pushup_mv.id,
                position=3,
                reps=200,
            ),
            WorkoutBlockMovementORM(
                workout_block_id=mu_main.id,
                movement_id=air_squat_mv.id,
                position=4,
                reps=300,
            ),
            WorkoutBlockMovementORM(
                workout_block_id=mu_main.id,
                movement_id=run_mv.id,
                position=5,
                distance_meters=1609,
            ),
        ]
    )

    # Helen blocks
    he2_warm = build_block(
        helen,
        1,
        "warmup",
        "Warm-up Helen",
        "Run suave + swings ligeros + algunas pull-ups tÃƒÂ©cnicas.",
    )
    he2_main = build_block(
        helen,
        2,
        "for_time",
        "Helen",
        "3 rounds: 400m run, 21 KB swings, 12 pull-ups",
        rounds=3,
    )
    session.add_all(
        [
            WorkoutBlockMovementORM(
                workout_block_id=he2_main.id,
                movement_id=run_mv.id,
                position=1,
                distance_meters=400,
            ),
            WorkoutBlockMovementORM(
                workout_block_id=he2_main.id,
                movement_id=kb_swing_mv.id,
                position=2,
                reps=21,
                load=24,
                load_unit="kg",
            ),
            WorkoutBlockMovementORM(
                workout_block_id=he2_main.id,
                movement_id=pullup_mv.id,
                position=3,
                reps=12,
            ),
        ]
    )

    # Karen blocks
    ka_warm = build_block(
        karen,
        1,
        "warmup",
        "Warm-up Karen",
        "Patterning de wall ball + movilidad tobillo/cadera.",
    )
    ka_main = build_block(
        karen,
        2,
        "for_time",
        "Karen",
        "150 wall balls",
    )
    session.add(
        WorkoutBlockMovementORM(
            workout_block_id=ka_main.id,
            movement_id=wb_mv.id,
            position=1,
            reps=150,
            load=9,
            load_unit="kg",
        )
    )

    # Cindy blocks
    ci_warm = build_block(
        cindy,
        1,
        "warmup",
        "Pre-Cindy",
        "Pull-ups fÃƒÂ¡ciles, push-ups y air squats suaves.",
    )
    ci_main = build_block(
        cindy,
        2,
        "amrap",
        "Cindy",
        "20 min AMRAP: 5 pull-ups, 10 push-ups, 15 air squats",
        duration_seconds=20 * 60,
    )
    session.add_all(
        [
            WorkoutBlockMovementORM(
                workout_block_id=ci_main.id,
                movement_id=pullup_mv.id,
                position=1,
                reps=5,
            ),
            WorkoutBlockMovementORM(
                workout_block_id=ci_main.id,
                movement_id=pushup_mv.id,
                position=2,
                reps=10,
            ),
            WorkoutBlockMovementORM(
                workout_block_id=ci_main.id,
                movement_id=air_squat_mv.id,
                position=3,
                reps=15,
            ),
        ]
    )

    # Equipamiento asociado a WODs
    session.add_all(
        [
            WorkoutEquipmentORM(workout_id=engine.id, equipment_id=rower.id),
            WorkoutEquipmentORM(workout_id=engine.id, equipment_id=kettlebell.id),

            WorkoutEquipmentORM(workout_id=hybrid.id, equipment_id=kettlebell.id),
            WorkoutEquipmentORM(workout_id=hybrid.id, equipment_id=box.id),

            WorkoutEquipmentORM(workout_id=strength.id, equipment_id=barbell.id),
            WorkoutEquipmentORM(workout_id=strength.id, equipment_id=kettlebell.id),

            WorkoutEquipmentORM(workout_id=hyrox_race.id, equipment_id=rower.id),
            WorkoutEquipmentORM(workout_id=hyrox_race.id, equipment_id=kettlebell.id),

            WorkoutEquipmentORM(workout_id=hyrox_sled.id, equipment_id=kettlebell.id),
            WorkoutEquipmentORM(workout_id=hyrox_wallballs.id, equipment_id=kettlebell.id),
            WorkoutEquipmentORM(workout_id=hyrox_engine.id, equipment_id=rower.id),
            WorkoutEquipmentORM(workout_id=hyrox_burpees.id, equipment_id=kettlebell.id),

            WorkoutEquipmentORM(workout_id=fran.id, equipment_id=barbell.id),
            WorkoutEquipmentORM(workout_id=murph.id, equipment_id=rig.id),
            WorkoutEquipmentORM(workout_id=helen.id, equipment_id=kettlebell.id),
            WorkoutEquipmentORM(workout_id=helen.id, equipment_id=rig.id),
            WorkoutEquipmentORM(workout_id=karen.id, equipment_id=kettlebell.id),
            WorkoutEquipmentORM(workout_id=cindy.id, equipment_id=rig.id),
        ]
    )


    # Training load last 5 days
    today = date.today()
    loads = []
    for i, vals in enumerate([(320, 300, 1.07), (340, 305, 1.11), (360, 310, 1.16), (310, 300, 1.03), (295, 298, 0.99)]):
        loads.append(
            UserTrainingLoadORM(
                user_id=user.id,
                load_date=today - timedelta(days=i),
                acute_load=vals[0],
                chronic_load=vals[1],
                load_ratio=vals[2],
                notes="Semana demo",
            )
        )
    session.add_all(loads)

    # Capacity profile
    session.add_all(
        [
            UserCapacityProfileORM(user_id=user.id, capacity_id=id_for(PhysicalCapacityORM, "Resistencia"), value=78, measured_at=datetime.utcnow()),
            UserCapacityProfileORM(user_id=user.id, capacity_id=id_for(PhysicalCapacityORM, "Fuerza"), value=72, measured_at=datetime.utcnow()),
            UserCapacityProfileORM(user_id=user.id, capacity_id=id_for(PhysicalCapacityORM, "Metcon"), value=75, measured_at=datetime.utcnow()),
            UserCapacityProfileORM(user_id=user.id, capacity_id=id_for(PhysicalCapacityORM, "Gimnásticos"), value=68, measured_at=datetime.utcnow()),
        ]
    )

    # Biometrics (3 days)
    session.add_all(
        [
            UserBiometricORM(user_id=user.id, measured_at=datetime.utcnow() - timedelta(days=2), hr_rest=48, hr_avg=62, hr_max=178, vo2_est=52, hrv=78, sleep_hours=7.4, fatigue_score=3.2, recovery_time_hours=1.4),
            UserBiometricORM(user_id=user.id, measured_at=datetime.utcnow() - timedelta(days=1), hr_rest=49, hr_avg=64, hr_max=176, vo2_est=51.5, hrv=75, sleep_hours=7.1, fatigue_score=3.5, recovery_time_hours=1.6),
            UserBiometricORM(user_id=user.id, measured_at=datetime.utcnow(), hr_rest=47, hr_avg=63, hr_max=180, vo2_est=52.3, hrv=79, sleep_hours=7.6, fatigue_score=3.0, recovery_time_hours=1.3),
        ]
    )

    # Skills
    session.add_all(
        [
            UserSkillORM(user_id=user.id, movement_id=row_mv.id, skill_score=82, note="Cadencia estable"),
            UserSkillORM(user_id=user.id, movement_id=kb_lunge_mv.id, skill_score=78, note="Control de paso"),
            UserSkillORM(user_id=user.id, movement_id=bbjo_mv.id, skill_score=70, note="Respiracion nasal"),
        ]
    )

    # PRs
    session.add_all(
        [
            UserPROM(user_id=user.id, movement_id=run_mv.id, pr_type="time", value=1172, unit="s", achieved_at=datetime.utcnow() - timedelta(days=30)),
            UserPROM(user_id=user.id, movement_id=row_mv.id, pr_type="time", value=420, unit="s", achieved_at=datetime.utcnow() - timedelta(days=20)),
            UserPROM(user_id=user.id, movement_id=dl_mv.id, pr_type="load", value=150, unit="kg", achieved_at=datetime.utcnow() - timedelta(days=10)),
        ]
    )

    # Achievements unlocked
    ach_rows = session.query(AchievementORM).all()
    session.add_all(
        [
            UserAchievementORM(user_id=user.id, achievement_id=ach_rows[0].id, unlocked_at=datetime.utcnow() - timedelta(days=7)),
            UserAchievementORM(user_id=user.id, achievement_id=ach_rows[1].id, unlocked_at=datetime.utcnow() - timedelta(days=3)),
            UserAchievementORM(user_id=user.id, achievement_id=ach_rows[2].id, unlocked_at=datetime.utcnow() - timedelta(days=1)),
        ]
    )

    # Missions assigned
    for mission in session.query(MissionORM).all():
        status = "assigned"
        progress = 0
        if mission.type == "daily":
            status = "completed"
            progress = 1
        elif mission.type == "weekly":
            status = "in_progress"
            progress = 2
        session.add(
            UserMissionORM(
                user_id=user.id,
                mission_id=mission.id,
                status=status,
                progress_value=progress,
                expires_at=datetime.utcnow() + timedelta(days=7 if mission.type != "daily" else 1),
                completed_at=datetime.utcnow() - timedelta(days=1) if status == "completed" else None,
            )
        )

    # Workout executions (5 sessions last 7 days)
    executions = []
    exec_blocks = []
    workouts_for_exec = [engine, hybrid, strength, engine, hybrid]
    for idx, w in enumerate(workouts_for_exec):
        executed_at = datetime.utcnow() - timedelta(days=idx)
        exec_row = WorkoutExecutionORM(
            workout_id=w.id,
            user_id=user.id,
            executed_at=executed_at,
            total_time_seconds=1100 + idx * 30,
            notes="Sesion demo",
        )
        session.add(exec_row)
        session.flush()
        # map to first two blocks of workout if exist
        blocks = session.query(WorkoutBlockORM).filter(WorkoutBlockORM.workout_id == w.id).order_by(WorkoutBlockORM.position).all()
        for b_idx, blk in enumerate(blocks[:2]):
            exec_blocks.append(
                WorkoutExecutionBlockORM(
                    execution_id=exec_row.id,
                    workout_block_id=blk.id,
                    time_seconds=300 + b_idx * 60,
                    hr_avg=150 + b_idx * 5,
                    hr_max=175 + b_idx * 3,
                    effort_score=7 + b_idx,
                )
            )
        executions.append(exec_row)
    session.add_all(exec_blocks)

    # Event demo
    event = EventORM(name="HYROX Madrid", date=today, location="Madrid", type="HYROX")
    session.add(event)
    session.flush()
    session.add(UserEventORM(user_id=user.id, event_id=event.id))

    session.commit()

