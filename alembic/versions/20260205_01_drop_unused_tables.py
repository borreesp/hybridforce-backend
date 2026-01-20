"""drop unused tables (events, training plans, global performance)

Revision ID: 20260205_01_drop_unused_tables
Revises: 20260111_01_add_workout_analysis
Create Date: 2026-02-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260205_01_drop_unused_tables"
down_revision = "20260111_01_add_workout_analysis"
branch_labels = None
depends_on = None


def upgrade():
    # Drop child tables first to respect FK constraints
    op.execute("DROP TABLE IF EXISTS user_event CASCADE")
    op.execute("DROP TABLE IF EXISTS training_plan_days CASCADE")
    op.execute("DROP TABLE IF EXISTS training_plans CASCADE")
    op.execute("DROP TABLE IF EXISTS movement_benchmarks CASCADE")
    op.execute("DROP TABLE IF EXISTS global_performance_data CASCADE")
    op.execute("DROP TABLE IF EXISTS events CASCADE")


def downgrade():
    # Recreate tables with original structure (minimal to allow rollback)
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("location", sa.String(length=100), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=True),
    )

    op.create_table(
        "training_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.create_table(
        "training_plan_days",
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("training_plans.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("day_number", sa.SmallInteger(), primary_key=True),
        sa.Column("focus", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.UniqueConstraint("plan_id", "day_number", name="uq_plan_day"),
    )

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
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("movement_id", "athlete_level_id", name="uq_movement_benchmark"),
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
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_global_perf_level", "global_performance_data", ["athlete_level_id"])

    op.create_table(
        "user_event",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
        sa.UniqueConstraint("user_id", "event_id", name="uq_user_event"),
    )
