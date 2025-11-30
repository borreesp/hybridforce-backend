from datetime import date

from infrastructure.db.models import (
    AthleteLevelORM,
    EnergyDomainORM,
    EquipmentORM,
    EventORM,
    HyroxStationORM,
    IntensityLevelORM,
    MovementMuscleORM,
    MovementORM,
    MuscleGroupORM,
    PhysicalCapacityORM,
    TrainingPlanDayORM,
    TrainingPlanORM,
    UserEventORM,
    UserORM,
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


def _ensure_lookup(session, model, records):
    for rec in records:
        existing = session.query(model).filter_by(code=rec["code"]).first()
        if not existing:
            session.add(model(**rec))
    session.flush()


def seed_data(session):
    if session.query(UserORM).count() > 0:
        return

    athlete_levels = [
        {"code": "Beginner", "name": "Beginner", "description": None, "sort_order": 1},
        {"code": "Intermedio", "name": "Intermedio", "description": None, "sort_order": 2},
        {"code": "RX", "name": "RX", "description": None, "sort_order": 3},
        {"code": "HYROX Competitor", "name": "HYROX Competitor", "description": None, "sort_order": 4},
    ]
    intensity_levels = [
        {"code": "Baja", "name": "Baja", "sort_order": 1},
        {"code": "Media", "name": "Media", "sort_order": 2},
        {"code": "Alta", "name": "Alta", "sort_order": 3},
    ]
    energy_domains = [
        {"code": "Aeróbico", "name": "Aeróbico", "description": None},
        {"code": "Anaeróbico", "name": "Anaeróbico", "description": None},
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

    def id_for(model, code):
        row = session.query(model).filter_by(code=code).first()
        return row.id if row else None

    user = UserORM(
        name="Lena Hybrid",
        email="lena@example.com",
        password="changeme",
        athlete_level_id=id_for(AthleteLevelORM, "Intermedio"),
    )

    rower = EquipmentORM(name="Rower", description="Concept2 rower", price=899.00, category="Cardio")
    sled = EquipmentORM(name="Sled", description="Prowler sled", price=450.00, category="HYROX")

    workout = WorkoutORM(
        title="Engine Builder",
        description="10 rounds: 200m row + 10 wall balls. Rest 1:00",
        domain_id=id_for(EnergyDomainORM, "Aeróbico"),
        intensity_level_id=id_for(IntensityLevelORM, "Media"),
        hyrox_transfer_level_id=id_for(IntensityLevelORM, "Media"),
        wod_type="Intervals",
        official_tag="HYROX friendly",
        main_muscle_group_id=id_for(MuscleGroupORM, "Posterior"),
    )
    session.add(workout)
    session.flush()

    workout.metadata_rel = WorkoutMetadataORM(
        workout_id=workout.id,
        volume_total="2000m row + 100 WB",
        work_rest_ratio="1:1",
        dominant_stimulus="Cardio",
        load_type="Light",
        athlete_profile_desc="Intermedio que necesita consistencia de ritmo",
        target_athlete_desc="Cualquier atleta mejorando pacing largo",
        pacing_tip="Divide en series suaves",
        pacing_detail="Mantén 70-75% esfuerzo en las primeras 5 rondas",
        break_tip="Respiro nasal en transición",
        rx_variant="Lleva la velocidad del row a 1:50-2:00",
        scaled_variant="Usa balón de 6-8kg y 150m row",
        ai_observation="Ideal para días de volumen controlado",
        session_load="Moderate",
        session_feel="Pulso elevado pero controlado",
    )
    workout.stats = WorkoutStatsORM(
        workout_id=workout.id,
        estimated_difficulty=6.5,
        avg_time_seconds=1200,
        rating_count=0,
    )

    workout.level_times = [
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "Beginner"), time_minutes=24.0, time_range="22-26"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "Intermedio"), time_minutes=20.0, time_range="19-21"),
        WorkoutLevelTimeORM(athlete_level_id=id_for(AthleteLevelORM, "RX"), time_minutes=18.0, time_range="17-19"),
    ]
    workout.capacities = [
        WorkoutCapacityORM(capacity_id=id_for(PhysicalCapacityORM, "Resistencia"), value=80, note="Ritmo sostenido en 10 rondas"),
        WorkoutCapacityORM(capacity_id=id_for(PhysicalCapacityORM, "Carga muscular"), value=55, note="Carga ligera, alto volumen"),
    ]
    workout.hyrox_stations = [
        WorkoutHyroxStationORM(station_id=id_for(HyroxStationORM, "Row"), transfer_pct=70),
        WorkoutHyroxStationORM(station_id=id_for(HyroxStationORM, "Wall Balls"), transfer_pct=60),
    ]
    workout.muscles = [
        WorkoutMuscleORM(muscle_group_id=id_for(MuscleGroupORM, "Piernas")),
        WorkoutMuscleORM(muscle_group_id=id_for(MuscleGroupORM, "Core")),
    ]

    warmup_block = WorkoutBlockORM(workout_id=workout.id, position=1, block_type="warmup", title="Calentamiento", description="Row easy pace")
    main_block = WorkoutBlockORM(
        workout_id=workout.id, position=2, block_type="intervals", title="10 rounds", description="200m row + 10 wall balls"
    )
    session.add_all([warmup_block, main_block])
    session.flush()

    row_movement = MovementORM(name="Row", category="Cardio", description="Row erg", default_load_unit=None)
    wb_movement = MovementORM(name="Wall Ball", category="Metcon", description="Wall ball shot", default_load_unit="kg")
    session.add_all([row_movement, wb_movement])
    session.flush()

    session.add_all(
        [
            MovementMuscleORM(movement_id=row_movement.id, muscle_group_id=id_for(MuscleGroupORM, "Posterior"), is_primary=True),
            MovementMuscleORM(movement_id=wb_movement.id, muscle_group_id=id_for(MuscleGroupORM, "Piernas"), is_primary=True),
        ]
    )

    session.add_all(
        [
            WorkoutBlockMovementORM(
                workout_block_id=main_block.id,
                movement_id=row_movement.id,
                position=1,
                distance_meters=200,
            ),
            WorkoutBlockMovementORM(
                workout_block_id=main_block.id,
                movement_id=wb_movement.id,
                position=2,
                reps=10,
                load=9,
                load_unit="kg",
            ),
        ]
    )

    plan = TrainingPlanORM(name="Starter HYROX Base", description="3 días de base aeróbica + fuerza")
    plan.days = [
        TrainingPlanDayORM(day_number=1, focus="Engine + Core", description="Row + core carry combo"),
        TrainingPlanDayORM(day_number=2, focus="Fuerza básica", description="Sentadillas y empuje"),
        TrainingPlanDayORM(day_number=3, focus="Metcon", description="AMRAP 15: burpees + lunges"),
    ]

    event = EventORM(name="HYROX Madrid", date=date.today(), location="Madrid", type="HYROX")

    session.add_all([user, rower, sled, plan, event])
    session.flush()

    session.add(UserEventORM(user_id=user.id, event_id=event.id))
    session.add(WorkoutEquipmentORM(workout_id=workout.id, equipment_id=rower.id))
    session.add(WorkoutEquipmentORM(workout_id=workout.id, equipment_id=sled.id))

    session.commit()
