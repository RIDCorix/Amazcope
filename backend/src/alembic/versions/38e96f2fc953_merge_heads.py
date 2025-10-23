"""merge_heads

Revision ID: 38e96f2fc953
Revises: 2821cc1df801, d41a4f47aa79
Create Date: 2025-10-23 15:28:39.889739

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "38e96f2fc953"
down_revision: str | Sequence[str] | None = ("2821cc1df801", "d41a4f47aa79")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
