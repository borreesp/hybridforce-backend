"""Introduce lookup tables and expanded workout model with blocks/movements/versioning."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251130_01_new_schema"
down_revision = None
branch_labels = None
depends_on = None


def _create_lookup_tables():
    op.create_table(
        "athlete_levels",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=True),
        sa.UniqueConstraint("code", name="uq_athlete_levels_code"),
    )
    op.create_index("ix_athlete_levels_sort", "athlete_levels", ["sort_order"])

    op.create_table(
        "intensity_levels",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=True),
        sa.UniqueConstraint("code", name="uq_intensity_levels_code"),
    )
    op.create_index("ix_intensity_levels_sort", "intensity_levels", ["sort_order"])

    op.create_table(
        "energy_domains",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.UniqueConstraint("code", name="uq_energy_domains_code"),
    )

    op.create_table(
        "physical_capacities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.UniqueConstraint("code", name="uq_physical_capacities_code"),
    )

    op.create_table(
        "muscle_groups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.UniqueConstraint("code", name="uq_muscle_groups_code"),
    )

    op.create_table(
        "hyrox_stations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.UniqueConstraint("code", name="uq_hyrox_stations_code"),
    )


def _seed_lookup_tables():
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
        INSERT INTO athlete_levels (code,name,description,sort_order) VALUES
        ('Beginner','Beginner',NULL,1),
        ('Intermedio','Intermedio',NULL,2),
        ('RX','RX',NULL,3),
        ('HYROX Competitor','HYROX Competitor',NULL,4)
        ON CONFLICT (code) DO NOTHING;
        """
        )
    )
    conn.execute(
        sa.text(
            """
        INSERT INTO intensity_levels (code,name,sort_order) VALUES
        ('Baja','Baja',1),
        ('Media','Media',2),
        ('Alta','Alta',3)
        ON CONFLICT (code) DO NOTHING;
        """
        )
    )
    conn.execute(
        sa.text(
            """
        INSERT INTO energy_domains (code,name,description) VALUES
        ('Aeróbico','Aeróbico',NULL),
        ('Anaeróbico','Anaeróbico',NULL),
        ('Mixto','Mixto',NULL)
        ON CONFLICT (code) DO NOTHING;
        """
        )
    )
    conn.execute(
        sa.text(
            """
        INSERT INTO physical_capacities (code,name,description) VALUES
        ('Fuerza','Fuerza',NULL),
        ('Resistencia','Resistencia',NULL),
        ('Velocidad','Velocidad',NULL),
        ('Gimnásticos','Gimnásticos',NULL),
        ('Metcon','Metcon',NULL),
        ('Carga muscular','Carga muscular',NULL)
        ON CONFLICT (code) DO NOTHING;
        """
        )
    )
    conn.execute(
        sa.text(
            """
        INSERT INTO muscle_groups (code,name,description) VALUES
        ('Piernas','Piernas',NULL),
        ('Core','Core',NULL),
        ('Hombros','Hombros',NULL),
        ('Posterior','Posterior',NULL),
        ('Grip','Grip',NULL),
        ('Pecho','Pecho',NULL),
        ('Brazos','Brazos',NULL)
        ON CONFLICT (code) DO NOTHING;
        """
        )
    )
    conn.execute(
        sa.text(
            """
        INSERT INTO hyrox_stations (code,name,description) VALUES
        ('SkiErg','SkiErg',NULL),
        ('Sled Push','Sled Push',NULL),
        ('Sled Pull','Sled Pull',NULL),
        ('Farmers Carry','Farmers Carry',NULL),
        ('Burpee Broad Jump','Burpee Broad Jump',NULL),
        ('Row','Row',NULL),
        ('Sandbag Lunges','Sandbag Lunges',NULL),
        ('Wall Balls','Wall Balls',NULL)
        ON CONFLICT (code) DO NOTHING;
        """
        )
    )


def _create_base_tables_if_absent(inspector):
    # users
    if not inspector.has_table("users"):
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("email", sa.String(length=100), nullable=False),
            sa.Column("password", sa.String(length=100), nullable=False),
            sa.Column("athlete_level_id", sa.Integer(), nullable=True),
            sa.UniqueConstraint("email", name="uq_users_email"),
        )
        op.create_foreign_key("fk_users_athlete_level", "users", "athlete_levels", ["athlete_level_id"], ["id"])

    # events
    if not inspector.has_table("events"):
        op.create_table(
            "events",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("date", sa.Date(), nullable=False),
            sa.Column("location", sa.String(length=100), nullable=False),
            sa.Column("type", sa.String(length=50), nullable=True),
        )

    # equipment
    if not inspector.has_table("equipment"):
        op.create_table(
            "equipment",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("price", sa.Numeric(6, 2), nullable=False),
            sa.Column("image_url", sa.Text(), nullable=True),
            sa.Column("category", sa.String(length=50), nullable=True),
        )

    # training plans
    if not inspector.has_table("training_plans"):
        op.create_table(
            "training_plans",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
        )
    if not inspector.has_table("training_plan_days"):
        op.create_table(
            "training_plan_days",
            sa.Column("plan_id", sa.Integer(), sa.ForeignKey("training_plans.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("day_number", sa.SmallInteger(), primary_key=True),
            sa.Column("focus", sa.String(length=100), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.UniqueConstraint("plan_id", "day_number", name="uq_plan_day"),
        )

    # workouts
    if not inspector.has_table("workouts"):
        op.create_table(
            "workouts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("parent_workout_id", sa.Integer(), nullable=True),
            sa.Column("version", sa.SmallInteger(), nullable=False, server_default="1"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("title", sa.String(length=100), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("domain_id", sa.Integer(), nullable=True),
            sa.Column("intensity_level_id", sa.Integer(), nullable=True),
            sa.Column("hyrox_transfer_level_id", sa.Integer(), nullable=True),
            sa.Column("wod_type", sa.String(length=100), nullable=False),
            sa.Column("official_tag", sa.String(length=50), nullable=True),
            sa.Column("main_muscle_group_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("parent_workout_id", "version", name="uq_workouts_version"),
        )
        op.create_index("ix_workouts_parent", "workouts", ["parent_workout_id"])
        op.create_foreign_key("fk_workouts_parent", "workouts", "workouts", ["parent_workout_id"], ["id"], ondelete="SET NULL")
        op.create_foreign_key("fk_workouts_domain", "workouts", "energy_domains", ["domain_id"], ["id"])
        op.create_foreign_key("fk_workouts_intensity", "workouts", "intensity_levels", ["intensity_level_id"], ["id"])
        op.create_foreign_key("fk_workouts_hyrox_transfer", "workouts", "intensity_levels", ["hyrox_transfer_level_id"], ["id"])
        op.create_foreign_key("fk_workouts_main_muscle", "workouts", "muscle_groups", ["main_muscle_group_id"], ["id"])

    # associations if absent
    if not inspector.has_table("user_event"):
        op.create_table(
            "user_event",
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
            sa.UniqueConstraint("user_id", "event_id", name="uq_user_event"),
        )
    if not inspector.has_table("workout_level_time"):
        op.create_table(
            "workout_level_time",
            sa.Column("workout_id", sa.Integer(), sa.ForeignKey("workouts.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("athlete_level_id", sa.Integer(), sa.ForeignKey("athlete_levels.id"), primary_key=True, nullable=True),
            sa.Column("time_minutes", sa.Numeric(4, 1), nullable=False),
            sa.Column("time_range", sa.String(length=20), nullable=False),
            sa.UniqueConstraint("workout_id", "athlete_level_id", name="uq_workout_level"),
        )
    if not inspector.has_table("workout_capacity"):
        op.create_table(
            "workout_capacity",
            sa.Column("workout_id", sa.Integer(), sa.ForeignKey("workouts.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("capacity_id", sa.Integer(), sa.ForeignKey("physical_capacities.id"), primary_key=True, nullable=True),
            sa.Column("value", sa.SmallInteger(), nullable=False),
            sa.Column("note", sa.Text(), nullable=False),
            sa.UniqueConstraint("workout_id", "capacity_id", name="uq_workout_capacity"),
        )
    if not inspector.has_table("workout_hyrox_station"):
        op.create_table(
            "workout_hyrox_station",
            sa.Column("workout_id", sa.Integer(), sa.ForeignKey("workouts.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("station_id", sa.Integer(), sa.ForeignKey("hyrox_stations.id"), primary_key=True, nullable=True),
            sa.Column("transfer_pct", sa.SmallInteger(), nullable=False),
            sa.UniqueConstraint("workout_id", "station_id", name="uq_workout_station"),
        )
    if not inspector.has_table("workout_muscle"):
        op.create_table(
            "workout_muscle",
            sa.Column("workout_id", sa.Integer(), sa.ForeignKey("workouts.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("muscle_group_id", sa.Integer(), sa.ForeignKey("muscle_groups.id"), primary_key=True, nullable=True),
            sa.UniqueConstraint("workout_id", "muscle_group_id", name="uq_workout_muscle"),
        )
    if not inspector.has_table("workout_equipment"):
        op.create_table(
            "workout_equipment",
            sa.Column("workout_id", sa.Integer(), sa.ForeignKey("workouts.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("equipment_id", sa.Integer(), sa.ForeignKey("equipment.id", ondelete="CASCADE"), primary_key=True),
            sa.UniqueConstraint("workout_id", "equipment_id", name="uq_workout_equipment"),
        )
    if not inspector.has_table("workout_result"):
        op.create_table(
            "workout_result",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("workout_id", sa.Integer(), sa.ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("time_seconds", sa.SmallInteger(), nullable=False),
            sa.Column("difficulty", sa.SmallInteger(), nullable=True),
            sa.Column("rating", sa.SmallInteger(), nullable=True),
            sa.Column("comment", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_workout_result_user", "workout_result", ["user_id"])
        op.create_index("ix_workout_result_workout", "workout_result", ["workout_id"])
    if not inspector.has_table("similar_workouts"):
        op.create_table(
            "similar_workouts",
            sa.Column("workout_id", sa.Integer(), sa.ForeignKey("workouts.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("similar_workout_id", sa.Integer(), sa.ForeignKey("workouts.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("note", sa.Text(), nullable=True),
            sa.UniqueConstraint("workout_id", "similar_workout_id", name="uq_similar_workout"),
            sa.CheckConstraint("workout_id <> similar_workout_id", name="ck_similar_not_same"),
            sa.CheckConstraint("workout_id < similar_workout_id", name="ck_similar_ordering"),
        )

def upgrade() -> None:
    _create_lookup_tables()
    _seed_lookup_tables()
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    _create_base_tables_if_absent(inspector)

    # New supporting tables (if not already created above)
    op.create_table(
        "user_training_load",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("load_date", sa.Date(), nullable=False),
        sa.Column("acute_load", sa.Numeric(8, 2), nullable=True),
        sa.Column("chronic_load", sa.Numeric(8, 2), nullable=True),
        sa.Column("load_ratio", sa.Numeric(5, 2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.UniqueConstraint("user_id", "load_date", name="uq_user_load_date"),
    )
    op.create_index("ix_user_training_load_user", "user_training_load", ["user_id"])

    op.create_table(
        "user_capacity_profile",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("capacity_id", sa.Integer(), sa.ForeignKey("physical_capacities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("value", sa.SmallInteger(), nullable=False),
        sa.Column("measured_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("user_id", "capacity_id", "measured_at", name="uq_user_capacity_measured"),
    )
    op.create_index("ix_user_capacity_user_capacity", "user_capacity_profile", ["user_id", "capacity_id"])

    # Add lookup FKs to existing tables (if they already existed without them)
    if "athlete_level_id" not in [c["name"] for c in inspector.get_columns("users")]:
        op.add_column("users", sa.Column("athlete_level_id", sa.Integer(), nullable=True))
        op.create_foreign_key("fk_users_athlete_level", "users", "athlete_levels", ["athlete_level_id"], ["id"])

    # workouts main table alterations
    workout_columns = [c["name"] for c in inspector.get_columns("workouts")]
    if "parent_workout_id" not in workout_columns:
        op.add_column("workouts", sa.Column("parent_workout_id", sa.Integer(), nullable=True))
    if "version" not in workout_columns:
        op.add_column("workouts", sa.Column("version", sa.SmallInteger(), nullable=False, server_default="1"))
    if "is_active" not in workout_columns:
        op.add_column("workouts", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    if "domain_id" not in workout_columns:
        op.add_column("workouts", sa.Column("domain_id", sa.Integer(), nullable=True))
    if "intensity_level_id" not in workout_columns:
        op.add_column("workouts", sa.Column("intensity_level_id", sa.Integer(), nullable=True))
    if "hyrox_transfer_level_id" not in workout_columns:
        op.add_column("workouts", sa.Column("hyrox_transfer_level_id", sa.Integer(), nullable=True))
    if "main_muscle_group_id" not in workout_columns:
        op.add_column("workouts", sa.Column("main_muscle_group_id", sa.Integer(), nullable=True))
    if "created_at" not in workout_columns:
        op.add_column("workouts", sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False))
    if "updated_at" not in workout_columns:
        op.add_column("workouts", sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False))
    existing_workout_fks = [fk["name"] for fk in inspector.get_foreign_keys("workouts")]
    if "fk_workouts_parent" not in existing_workout_fks:
        op.create_foreign_key("fk_workouts_parent", "workouts", "workouts", ["parent_workout_id"], ["id"], ondelete="SET NULL")
    if "fk_workouts_domain" not in existing_workout_fks:
        op.create_foreign_key("fk_workouts_domain", "workouts", "energy_domains", ["domain_id"], ["id"])
    if "fk_workouts_intensity" not in existing_workout_fks:
        op.create_foreign_key("fk_workouts_intensity", "workouts", "intensity_levels", ["intensity_level_id"], ["id"])
    if "fk_workouts_hyrox_transfer" not in existing_workout_fks:
        op.create_foreign_key("fk_workouts_hyrox_transfer", "workouts", "intensity_levels", ["hyrox_transfer_level_id"], ["id"])
    if "fk_workouts_main_muscle" not in existing_workout_fks:
        op.create_foreign_key("fk_workouts_main_muscle", "workouts", "muscle_groups", ["main_muscle_group_id"], ["id"])
    if "uq_workouts_version" not in [c["name"] for c in inspector.get_unique_constraints("workouts")]:
        op.create_unique_constraint("uq_workouts_version", "workouts", ["parent_workout_id", "version"])
    if "ix_workouts_parent" not in [i["name"] for i in inspector.get_indexes("workouts")]:
        op.create_index("ix_workouts_parent", "workouts", ["parent_workout_id"])

    # Split metadata/stats tables
    op.create_table(
        "workout_metadata",
        sa.Column("workout_id", sa.Integer(), sa.ForeignKey("workouts.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("volume_total", sa.Text(), nullable=True),
        sa.Column("work_rest_ratio", sa.Text(), nullable=True),
        sa.Column("dominant_stimulus", sa.Text(), nullable=True),
        sa.Column("load_type", sa.Text(), nullable=True),
        sa.Column("athlete_profile_desc", sa.Text(), nullable=True),
        sa.Column("target_athlete_desc", sa.Text(), nullable=True),
        sa.Column("pacing_tip", sa.Text(), nullable=True),
        sa.Column("pacing_detail", sa.Text(), nullable=True),
        sa.Column("break_tip", sa.Text(), nullable=True),
        sa.Column("rx_variant", sa.Text(), nullable=True),
        sa.Column("scaled_variant", sa.Text(), nullable=True),
        sa.Column("ai_observation", sa.Text(), nullable=True),
        sa.Column("session_load", sa.Text(), nullable=True),
        sa.Column("session_feel", sa.Text(), nullable=True),
        sa.Column("extra_attributes_json", postgresql.JSONB(), nullable=True),
    )
    op.create_table(
        "workout_stats",
        sa.Column("workout_id", sa.Integer(), sa.ForeignKey("workouts.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("estimated_difficulty", sa.Numeric(3, 1), nullable=True),
        sa.Column("avg_time_seconds", sa.SmallInteger(), nullable=True),
        sa.Column("avg_rating", sa.Numeric(3, 2), nullable=True),
        sa.Column("avg_difficulty", sa.Numeric(3, 1), nullable=True),
        sa.Column("rating_count", sa.Integer(), nullable=True),
    )

    # Add lookup FK columns to detail tables
    if inspector.has_table("workout_level_time") and "athlete_level_id" not in [c["name"] for c in inspector.get_columns("workout_level_time")]:
        op.add_column("workout_level_time", sa.Column("athlete_level_id", sa.Integer(), nullable=True))
        op.create_foreign_key("fk_workout_level_time_level", "workout_level_time", "athlete_levels", ["athlete_level_id"], ["id"])
    if inspector.has_table("workout_capacity") and "capacity_id" not in [c["name"] for c in inspector.get_columns("workout_capacity")]:
        op.add_column("workout_capacity", sa.Column("capacity_id", sa.Integer(), nullable=True))
        op.create_foreign_key("fk_workout_capacity_capacity", "workout_capacity", "physical_capacities", ["capacity_id"], ["id"])
    if inspector.has_table("workout_hyrox_station") and "station_id" not in [c["name"] for c in inspector.get_columns("workout_hyrox_station")]:
        op.add_column("workout_hyrox_station", sa.Column("station_id", sa.Integer(), nullable=True))
        op.create_foreign_key("fk_workout_station", "workout_hyrox_station", "hyrox_stations", ["station_id"], ["id"])
    if inspector.has_table("workout_muscle") and "muscle_group_id" not in [c["name"] for c in inspector.get_columns("workout_muscle")]:
        op.add_column("workout_muscle", sa.Column("muscle_group_id", sa.Integer(), nullable=True))
        op.create_foreign_key("fk_workout_muscle_group", "workout_muscle", "muscle_groups", ["muscle_group_id"], ["id"])

    # New movement / block tables
    op.create_table(
        "movements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("default_load_unit", sa.String(length=20), nullable=True),
        sa.Column("video_url", sa.Text(), nullable=True),
        sa.UniqueConstraint("name", name="uq_movements_name"),
    )
    op.create_table(
        "movement_muscles",
        sa.Column("movement_id", sa.Integer(), sa.ForeignKey("movements.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("muscle_group_id", sa.Integer(), sa.ForeignKey("muscle_groups.id"), primary_key=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("movement_id", "muscle_group_id", name="uq_movement_muscle"),
    )
    op.create_table(
        "workout_blocks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("workout_id", sa.Integer(), sa.ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("block_type", sa.String(length=50), nullable=True),
        sa.Column("title", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("rounds", sa.SmallInteger(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.UniqueConstraint("workout_id", "position", name="uq_workout_block_position"),
    )
    op.create_table(
        "workout_block_movements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("workout_block_id", sa.Integer(), sa.ForeignKey("workout_blocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("movement_id", sa.Integer(), sa.ForeignKey("movements.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("reps", sa.Numeric(6, 2), nullable=True),
        sa.Column("load", sa.Numeric(6, 2), nullable=True),
        sa.Column("load_unit", sa.String(length=20), nullable=True),
        sa.Column("distance_meters", sa.Numeric(8, 2), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("calories", sa.Numeric(6, 2), nullable=True),
        sa.UniqueConstraint("workout_block_id", "position", name="uq_block_movement_position"),
        sa.CheckConstraint(
            "(reps IS NOT NULL) OR (load IS NOT NULL) OR (distance_meters IS NOT NULL) OR (duration_seconds IS NOT NULL) OR (calories IS NOT NULL)",
            name="ck_block_movement_metrics_not_all_null",
        ),
    )

    # Adjust constraints on existing tables (only if missing)
    existing_ck = {ck["name"] for ck in inspector.get_check_constraints("similar_workouts")} if inspector.has_table("similar_workouts") else set()
    if inspector.has_table("similar_workouts") and "ck_similar_not_same" not in existing_ck:
        op.create_check_constraint("ck_similar_not_same", "similar_workouts", "workout_id <> similar_workout_id")
    if inspector.has_table("similar_workouts") and "ck_similar_ordering" not in existing_ck:
        op.create_check_constraint("ck_similar_ordering", "similar_workouts", "workout_id < similar_workout_id")

    # Data migration: map enums to lookup FKs
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    for table, col, lookup in [
        ("users", "athlete_level", "athlete_levels"),
        ("workouts", "domain", "energy_domains"),
        ("workouts", "intensity", "intensity_levels"),
        ("workouts", "hyrox_transfer", "intensity_levels"),
        ("workout_level_time", "athlete_level", "athlete_levels"),
        ("workout_capacity", "capacity", "physical_capacities"),
        ("workout_hyrox_station", "station", "hyrox_stations"),
        ("workout_muscle", "muscle", "muscle_groups"),
    ]:
        cols = [c["name"] for c in inspector.get_columns(table)] if inspector.has_table(table) else []
        if inspector.has_table(table) and lookup and inspector.has_table(lookup) and col in cols:
            conn.execute(
                sa.text(
                    f"""
                    UPDATE {table} t
                    SET {col}_id = l.id
                    FROM {lookup} l
                    WHERE t.{col}::text = l.code
                    """
                )
            )

    # Move workout metadata and stats to new tables only if legacy columns exist
    workout_cols = [c["name"] for c in inspector.get_columns("workouts")] if inspector.has_table("workouts") else []
    meta_fields = [
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
    ]
    stats_fields = ["estimated_difficulty", "avg_time_seconds", "avg_rating", "avg_difficulty", "rating_count"]
    if inspector.has_table("workouts") and all(f in workout_cols for f in meta_fields):
        conn.execute(
            sa.text(
                """
                INSERT INTO workout_metadata (workout_id, volume_total, work_rest_ratio, dominant_stimulus, load_type,
                                              athlete_profile_desc, target_athlete_desc, pacing_tip, pacing_detail,
                                              break_tip, rx_variant, scaled_variant, ai_observation, session_load, session_feel)
                SELECT id, volume_total, work_rest_ratio, dominant_stimulus, load_type, athlete_profile_desc, target_athlete_desc,
                       pacing_tip, pacing_detail, break_tip, rx_variant, scaled_variant, ai_observation, session_load, session_feel
                FROM workouts
                ON CONFLICT (workout_id) DO NOTHING;
                """
            )
        )
    if inspector.has_table("workouts") and all(f in workout_cols for f in stats_fields):
        conn.execute(
            sa.text(
                """
                INSERT INTO workout_stats (workout_id, estimated_difficulty, avg_time_seconds, avg_rating, avg_difficulty, rating_count)
                SELECT id, estimated_difficulty, avg_time_seconds, avg_rating, avg_difficulty, rating_count
                FROM workouts
                ON CONFLICT (workout_id) DO NOTHING;
                """
            )
        )

    # workout_result created_at
    if inspector.has_table("workout_result") and "created_at" not in [c["name"] for c in inspector.get_columns("workout_result")]:
        op.add_column("workout_result", sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False))
    if inspector.has_table("workout_result") and "ix_workout_result_user" not in [i["name"] for i in inspector.get_indexes("workout_result")]:
        op.create_index("ix_workout_result_user", "workout_result", ["user_id"])
    if inspector.has_table("workout_result") and "ix_workout_result_workout" not in [i["name"] for i in inspector.get_indexes("workout_result")]:
        op.create_index("ix_workout_result_workout", "workout_result", ["workout_id"])

    # Drop old enum-based columns now migrated
    if inspector.has_table("users"):
        existing_cols = [c["name"] for c in inspector.get_columns("users")]
        if "athlete_level" in existing_cols:
            op.drop_column("users", "athlete_level")

    if inspector.has_table("workouts"):
        existing_cols = [c["name"] for c in inspector.get_columns("workouts")]
        for col in [
            "domain",
            "intensity",
            "hyrox_transfer",
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
            "avg_time_seconds",
            "avg_rating",
            "avg_difficulty",
            "rating_count",
            "estimated_difficulty",
            "main_muscle_chain",
        ]:
            if col in existing_cols:
                op.drop_column("workouts", col)

    if inspector.has_table("workout_level_time"):
        existing_cols = [c["name"] for c in inspector.get_columns("workout_level_time")]
        if "athlete_level" in existing_cols:
            op.drop_column("workout_level_time", "athlete_level")
    if inspector.has_table("workout_capacity"):
        existing_cols = [c["name"] for c in inspector.get_columns("workout_capacity")]
        if "capacity" in existing_cols:
            op.drop_column("workout_capacity", "capacity")
    if inspector.has_table("workout_hyrox_station"):
        existing_cols = [c["name"] for c in inspector.get_columns("workout_hyrox_station")]
        if "station" in existing_cols:
            op.drop_column("workout_hyrox_station", "station")
    if inspector.has_table("workout_muscle"):
        existing_cols = [c["name"] for c in inspector.get_columns("workout_muscle")]
        if "muscle" in existing_cols:
            op.drop_column("workout_muscle", "muscle")

    # Drop old ENUM types if they exist
    for enum_type in ["energy_domain", "intensity_level", "hyrox_transfer_level", "athlete_level", "workout_level_athlete_level", "workout_capacity_enum", "hyrox_station", "muscle_group"]:
        op.execute(f"DO $$ BEGIN IF EXISTS (SELECT 1 FROM pg_type WHERE typname = '{enum_type}') THEN DROP TYPE {enum_type}; END IF; END $$;")


def downgrade() -> None:
    # The downgrade will drop new tables and columns; restoring enums is out of scope.
    op.drop_table("workout_block_movements")
    op.drop_table("workout_blocks")
    op.drop_table("movement_muscles")
    op.drop_table("movements")
    op.drop_constraint("ck_similar_ordering", "similar_workouts", type_="check")
    op.drop_constraint("ck_similar_not_same", "similar_workouts", type_="check")

    if sa.inspect(op.get_bind()).has_table("workout_result"):
        with op.batch_alter_table("workout_result") as batch:
            if "created_at" in [c.name for c in batch.get_columns()]:
                batch.drop_column("created_at")
    op.drop_index("ix_workout_result_user", table_name="workout_result")
    op.drop_index("ix_workout_result_workout", table_name="workout_result")

    # Detail tables columns
    with op.batch_alter_table("workout_muscle") as batch:
        if "muscle_group_id" in [c.name for c in batch.get_columns()]:
            batch.drop_constraint("fk_workout_muscle_group", type_="foreignkey")
            batch.drop_column("muscle_group_id")
    with op.batch_alter_table("workout_hyrox_station") as batch:
        if "station_id" in [c.name for c in batch.get_columns()]:
            batch.drop_constraint("fk_workout_station", type_="foreignkey")
            batch.drop_column("station_id")
    with op.batch_alter_table("workout_capacity") as batch:
        if "capacity_id" in [c.name for c in batch.get_columns()]:
            batch.drop_constraint("fk_workout_capacity_capacity", type_="foreignkey")
            batch.drop_column("capacity_id")
    with op.batch_alter_table("workout_level_time") as batch:
        if "athlete_level_id" in [c.name for c in batch.get_columns()]:
            batch.drop_constraint("fk_workout_level_time_level", type_="foreignkey")
            batch.drop_column("athlete_level_id")

    op.drop_table("workout_stats")
    op.drop_table("workout_metadata")

    with op.batch_alter_table("workouts") as batch:
        for col in [
            "parent_workout_id",
            "version",
            "is_active",
            "domain_id",
            "intensity_level_id",
            "hyrox_transfer_level_id",
            "main_muscle_group_id",
            "created_at",
            "updated_at",
        ]:
            if col in [c.name for c in batch.get_columns()]:
                batch.drop_column(col)
        batch.drop_constraint("uq_workouts_version", type_="unique")
    op.drop_index("ix_workouts_parent", table_name="workouts")
    op.drop_constraint("fk_workouts_parent", "workouts", type_="foreignkey")
    op.drop_constraint("fk_workouts_domain", "workouts", type_="foreignkey")
    op.drop_constraint("fk_workouts_intensity", "workouts", type_="foreignkey")
    op.drop_constraint("fk_workouts_hyrox_transfer", "workouts", type_="foreignkey")
    op.drop_constraint("fk_workouts_main_muscle", "workouts", type_="foreignkey")

    op.drop_constraint("fk_users_athlete_level", "users", type_="foreignkey")
    op.drop_column("users", "athlete_level_id")

    op.drop_table("user_capacity_profile")
    op.drop_table("user_training_load")

    op.drop_table("hyrox_stations")
    op.drop_table("muscle_groups")
    op.drop_table("physical_capacities")
    op.drop_table("energy_domains")
    op.drop_index("ix_intensity_levels_sort", table_name="intensity_levels")
    op.drop_table("intensity_levels")
    op.drop_index("ix_athlete_levels_sort", table_name="athlete_levels")
    op.drop_table("athlete_levels")
