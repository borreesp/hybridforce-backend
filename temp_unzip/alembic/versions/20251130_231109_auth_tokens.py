"""Add token_version to users for auth invalidation."""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251130_231109_auth_tokens"
down_revision = "20251130_01_new_schema"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"))


def downgrade():
    op.drop_column("users", "token_version")
