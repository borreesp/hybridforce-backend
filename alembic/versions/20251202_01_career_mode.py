"""Add career mode, progress, achievements, missions, executions and benchmarks."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251202_01_career_mode"
down_revision = "20251130_231109_auth_tokens"
branch_labels = None
depends_on = None


def upgrade():
    # Extend athlete levels with XP ranges
    op.add_column("athlete_levels", sa.Column("min_xp", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("athlete_levels", sa.Column("max_xp", sa.Integer(), nullable=False, server_default="0"))

    # User progression and skills/biometrics
    op.create_table(
        "user_progress",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, nullable=False),
        sa.Column("xp_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("progress_pct", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "user_skills",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("movement_id", sa.Integer(), sa.ForeignKey("movements.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("measured_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_user_skills_user", "user_skills", ["user_id"])
    op.create_table(
        "user_biometrics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.func.now()),
        sa.Column("hr_rest", sa.Numeric(6, 2), nullable=True),
        sa.Column("hr_avg", sa.Numeric(6, 2), nullable=True),
        sa.Column("hr_max", sa.Numeric(6, 2), nullable=True),
        sa.Column("vo2_est", sa.Numeric(6, 2), nullable=True),
        sa.Column("hrv", sa.Numeric(6, 2), nullable=True),
        sa.Column("sleep_hours", sa.Numeric(4, 2), nullable=True),
        sa.Column("fatigue_score", sa.Numeric(4, 2), nullable=True),
        sa.Column("recovery_time_hours", sa.Numeric(6, 2), nullable=True),
    )
    op.create_index("ix_user_biometrics_user", "user_biometrics", ["user_id"])
    op.create_table(
        "user_pr",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("movement_id", sa.Integer(), sa.ForeignKey("movements.id", ondelete="CASCADE"), nullable=False),
        sa.Column("pr_type", sa.String(length=30), nullable=False),
        sa.Column("value", sa.Numeric(10, 2), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=True),
        sa.Column("achieved_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "movement_id", "pr_type", name="uq_user_pr_unique"),
    )
    op.create_index("ix_user_pr_user", "user_pr", ["user_id"])

    # Executions of workouts
    op.create_table(
        "workout_execution",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("workout_id", sa.Integer(), sa.ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("executed_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.func.now()),
        sa.Column("total_time_seconds", sa.Numeric(8, 2), nullable=True),
        sa.Column("raw_ocr_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("image_path", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_workout_execution_user", "workout_execution", ["user_id"])
    op.create_table(
        "workout_execution_block",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("execution_id", sa.Integer(), sa.ForeignKey("workout_execution.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workout_block_id", sa.Integer(), sa.ForeignKey("workout_blocks.id", ondelete="CASCADE"), nullable=True),
        sa.Column("time_seconds", sa.Numeric(8, 2), nullable=True),
        sa.Column("hr_avg", sa.Numeric(6, 2), nullable=True),
        sa.Column("hr_max", sa.Numeric(6, 2), nullable=True),
        sa.Column("effort_score", sa.Numeric(5, 2), nullable=True),
    )
    op.create_index("ix_workout_execution_block_exec", "workout_execution_block", ["execution_id"])

    # Benchmarks and stats by level
    op.create_table(
        "workout_stats_by_level",
        sa.Column("workout_id", sa.Integer(), sa.ForeignKey("workouts.id", ondelete="CASCADE"), primary_key=True, nullable=False),
        sa.Column("athlete_level_id", sa.Integer(), sa.ForeignKey("athlete_levels.id"), primary_key=True, nullable=False),
        sa.Column("avg_time_seconds", sa.Numeric(8, 2), nullable=True),
        sa.Column("median_time_seconds", sa.Numeric(8, 2), nullable=True),
        sa.Column("percentile_10", sa.Numeric(8, 2), nullable=True),
        sa.Column("percentile_90", sa.Numeric(8, 2), nullable=True),
        sa.Column("avg_difficulty", sa.Numeric(4, 2), nullable=True),
        sa.Column("sample_size", sa.Integer(), nullable=True),
    )
    op.create_table(
        "global_performance_data",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("workout_id", sa.Integer(), sa.ForeignKey("workouts.id", ondelete="CASCADE"), nullable=True),
        sa.Column("movement_id", sa.Integer(), sa.ForeignKey("movements.id", ondelete="CASCADE"), nullable=True),
        sa.Column("athlete_level_id", sa.Integer(), sa.ForeignKey("athlete_levels.id"), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=True),
        sa.Column("avg_time_seconds", sa.Numeric(8, 2), nullable=True),
        sa.Column("avg_reps", sa.Numeric(8, 2), nullable=True),
        sa.Column("avg_load", sa.Numeric(8, 2), nullable=True),
        sa.Column("percentile_25", sa.Numeric(8, 2), nullable=True),
        sa.Column("percentile_50", sa.Numeric(8, 2), nullable=True),
        sa.Column("percentile_75", sa.Numeric(8, 2), nullable=True),
        sa.Column("percentile_90", sa.Numeric(8, 2), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_global_perf_level", "global_performance_data", ["athlete_level_id"])

    op.create_table(
        "movement_benchmarks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("movement_id", sa.Integer(), sa.ForeignKey("movements.id", ondelete="CASCADE"), nullable=False),
        sa.Column("athlete_level_id", sa.Integer(), sa.ForeignKey("athlete_levels.id"), nullable=False),
        sa.Column("avg_score", sa.Numeric(8, 2), nullable=True),
        sa.Column("percentile_25", sa.Numeric(8, 2), nullable=True),
        sa.Column("percentile_50", sa.Numeric(8, 2), nullable=True),
        sa.Column("percentile_75", sa.Numeric(8, 2), nullable=True),
        sa.Column("percentile_90", sa.Numeric(8, 2), nullable=True),
        sa.Column("unit", sa.String(length=20), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_movement_benchmark", "movement_benchmarks", ["movement_id", "athlete_level_id"])

    op.create_table(
        "global_capacity_benchmarks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("capacity_id", sa.Integer(), sa.ForeignKey("physical_capacities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("athlete_level_id", sa.Integer(), sa.ForeignKey("athlete_levels.id"), nullable=False),
        sa.Column("avg_value", sa.Numeric(8, 2), nullable=True),
        sa.Column("percentile_50", sa.Numeric(8, 2), nullable=True),
        sa.Column("percentile_90", sa.Numeric(8, 2), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_global_capacity_bench", "global_capacity_benchmarks", ["capacity_id", "athlete_level_id"])

    # Achievements and missions
    op.create_table(
        "achievements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.Column("xp_reward", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("icon_url", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("code", name="uq_achievements_code"),
    )
    op.create_table(
        "user_achievements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("achievement_id", sa.Integer(), sa.ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False),
        sa.Column("unlocked_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),
    )
    op.create_index("ix_user_achievements_user", "user_achievements", ["user_id"])

    op.create_table(
        "missions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("xp_reward", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("condition_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_table(
        "user_missions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mission_id", sa.Integer(), sa.ForeignKey("missions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="assigned"),
        sa.Column("progress_value", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("assigned_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=False), nullable=True),
        sa.UniqueConstraint("user_id", "mission_id", name="uq_user_mission"),
    )
    op.create_index("ix_user_missions_user", "user_missions", ["user_id"])


def downgrade():
    op.drop_index("ix_user_missions_user", table_name="user_missions")
    op.drop_table("user_missions")
    op.drop_table("missions")
    op.drop_index("ix_user_achievements_user", table_name="user_achievements")
    op.drop_table("user_achievements")
    op.drop_table("achievements")
    op.drop_constraint("uq_global_capacity_bench", "global_capacity_benchmarks", type_="unique")
    op.drop_table("global_capacity_benchmarks")
    op.drop_constraint("uq_movement_benchmark", "movement_benchmarks", type_="unique")
    op.drop_table("movement_benchmarks")
    op.drop_index("ix_global_perf_level", table_name="global_performance_data")
    op.drop_table("global_performance_data")
    op.drop_table("workout_stats_by_level")
    op.drop_index("ix_workout_execution_block_exec", table_name="workout_execution_block")
    op.drop_table("workout_execution_block")
    op.drop_index("ix_workout_execution_user", table_name="workout_execution")
    op.drop_table("workout_execution")
    op.drop_index("ix_user_pr_user", table_name="user_pr")
    op.drop_table("user_pr")
    op.drop_index("ix_user_biometrics_user", table_name="user_biometrics")
    op.drop_table("user_biometrics")
    op.drop_index("ix_user_skills_user", table_name="user_skills")
    op.drop_table("user_skills")
    op.drop_table("user_progress")
    op.drop_column("athlete_levels", "max_xp")
    op.drop_column("athlete_levels", "min_xp")
