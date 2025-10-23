"""empty message

Revision ID: d41a4f47aa79
Revises: fd2c4d97639a
Create Date: 2025-10-23 11:41:33.117404

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "d41a4f47aa79"
down_revision: str | Sequence[str] | None = "fd2c4d97639a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
