"""add workout_analysis table

Revision ID: 20260111_01_add_workout_analysis
Revises: 20251202_01_career_mode
Create Date: 2026-01-11 18:20:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260111_01_add_workout_analysis"
down_revision = "20251202_01_career_mode"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "workout_analysis",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("workout_id", sa.Integer(), sa.ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analysis_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("athlete_impact", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("applied", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("applied_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_workout_analysis_user", "workout_analysis", ["user_id"])


def downgrade():
    op.drop_index("ix_workout_analysis_user", table_name="workout_analysis")
    op.drop_table("workout_analysis")
