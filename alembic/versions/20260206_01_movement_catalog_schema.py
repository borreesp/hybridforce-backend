"""Add movement aliases and metric flags.

Revision ID: 20260206_01_mov_catalog
Revises: 20260205_moves_ext
Create Date: 2026-02-06
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260206_01_mov_catalog"
down_revision = "20260205_moves_ext"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "movement_aliases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("movement_id", sa.Integer(), sa.ForeignKey("movements.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alias", sa.String(length=120), nullable=False),
        sa.Column("alias_normalized", sa.String(length=120), nullable=False),
        sa.Column("source", sa.String(length=30), nullable=True),
        sa.UniqueConstraint("movement_id", "alias_normalized", name="uq_movement_alias_normalized"),
    )
    op.create_index("ix_movement_aliases_alias_normalized", "movement_aliases", ["alias_normalized"])
    op.create_index("ix_movement_aliases_movement_id", "movement_aliases", ["movement_id"])

    op.add_column("movements", sa.Column("code", sa.String(length=80), nullable=True))
    op.add_column("movements", sa.Column("pattern", sa.String(length=50), nullable=True))
    op.add_column("movements", sa.Column("default_metric_unit", sa.String(length=20), nullable=True))
    op.add_column(
        "movements",
        sa.Column("supports_reps", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "movements",
        sa.Column("supports_load", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "movements",
        sa.Column("supports_distance", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "movements",
        sa.Column("supports_time", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "movements",
        sa.Column("supports_calories", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column("movements", sa.Column("skill_level", sa.String(length=20), nullable=True))

    op.create_unique_constraint("uq_movements_code", "movements", ["code"])
    op.create_index("ix_movements_code", "movements", ["code"])
    op.create_index("ix_movements_category", "movements", ["category"])
    op.create_index("ix_movements_pattern", "movements", ["pattern"])


def downgrade():
    op.drop_index("ix_movements_pattern", table_name="movements")
    op.drop_index("ix_movements_category", table_name="movements")
    op.drop_index("ix_movements_code", table_name="movements")
    op.drop_constraint("uq_movements_code", "movements", type_="unique")

    op.drop_column("movements", "skill_level")
    op.drop_column("movements", "supports_calories")
    op.drop_column("movements", "supports_time")
    op.drop_column("movements", "supports_distance")
    op.drop_column("movements", "supports_load")
    op.drop_column("movements", "supports_reps")
    op.drop_column("movements", "default_metric_unit")
    op.drop_column("movements", "pattern")
    op.drop_column("movements", "code")

    op.drop_index("ix_movement_aliases_movement_id", table_name="movement_aliases")
    op.drop_index("ix_movement_aliases_alias_normalized", table_name="movement_aliases")
    op.drop_table("movement_aliases")

