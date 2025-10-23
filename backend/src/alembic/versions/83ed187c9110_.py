"""empty message

Revision ID: 83ed187c9110
Revises: c4fef48e2d17
Create Date: 2025-10-22 13:21:22.771695

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "83ed187c9110"
down_revision: str | Sequence[str] | None = "c4fef48e2d17"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
