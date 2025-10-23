"""empty message

Revision ID: c4fef48e2d17
Revises:
Create Date: 2025-10-22 13:19:17.326353

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "c4fef48e2d17"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
