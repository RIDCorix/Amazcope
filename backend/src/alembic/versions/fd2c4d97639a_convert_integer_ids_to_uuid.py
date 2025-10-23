"""convert_integer_ids_to_uuid

Revision ID: fd2c4d97639a
Revises: 566deb65a87e
Create Date: 2025-10-22 11:22:16.140863

CRITICAL: This migration converts all integer primary keys to UUIDs.
This is a destructive migration - backup your data before running.

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op  # type: ignore[attr-defined]

# revision identifiers, used by Alembic.
revision: str = "fd2c4d97639a"
down_revision: str | Sequence[str] | None = "83ed187c9110"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Convert integer IDs to UUIDs.

    This migration:
    1. Adds UUID extension
    2. Adds new UUID columns
    3. Generates UUIDs for existing records
    4. Updates foreign key references
    5. Drops old integer columns and constraints
    6. Renames UUID columns to 'id'
    7. Recreates constraints and indexes
    """
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Step 1: Add new UUID columns to all tables
    # Users table
    op.add_column("users", sa.Column("id_uuid", UUID(as_uuid=True), nullable=True))
    op.execute("UPDATE users SET id_uuid = uuid_generate_v4()")
    op.alter_column("users", "id_uuid", nullable=False)

    # User Settings table
    op.add_column("user_settings", sa.Column("id_uuid", UUID(as_uuid=True), nullable=True))
    op.add_column("user_settings", sa.Column("user_id_uuid", UUID(as_uuid=True), nullable=True))
    op.execute("UPDATE user_settings SET id_uuid = uuid_generate_v4()")
    op.execute(
        """
        UPDATE user_settings SET user_id_uuid = users.id_uuid
        FROM users WHERE user_settings.user_id = users.id
    """
    )
    op.alter_column("user_settings", "id_uuid", nullable=False)
    op.alter_column("user_settings", "user_id_uuid", nullable=False)

    # Products table
    op.add_column("products", sa.Column("id_uuid", UUID(as_uuid=True), nullable=True))
    op.add_column("products", sa.Column("created_by_id_uuid", UUID(as_uuid=True), nullable=True))
    op.execute("UPDATE products SET id_uuid = uuid_generate_v4()")
    op.execute(
        """
        UPDATE products SET created_by_id_uuid = users.id_uuid
        FROM users WHERE products.created_by_id = users.id AND products.created_by_id IS NOT NULL
    """
    )
    op.alter_column("products", "id_uuid", nullable=False)

    # Product Snapshots table
    op.add_column("product_snapshots", sa.Column("id_uuid", UUID(as_uuid=True), nullable=True))
    op.add_column(
        "product_snapshots",
        sa.Column("product_id_uuid", UUID(as_uuid=True), nullable=True),
    )
    op.execute("UPDATE product_snapshots SET id_uuid = uuid_generate_v4()")
    op.execute(
        """
        UPDATE product_snapshots SET product_id_uuid = products.id_uuid
        FROM products WHERE product_snapshots.product_id = products.id
    """
    )
    op.alter_column("product_snapshots", "id_uuid", nullable=False)
    op.alter_column("product_snapshots", "product_id_uuid", nullable=False)

    # User Products table (junction table)
    op.add_column("user_products", sa.Column("id_uuid", UUID(as_uuid=True), nullable=True))
    op.add_column("user_products", sa.Column("user_id_uuid", UUID(as_uuid=True), nullable=True))
    op.add_column("user_products", sa.Column("product_id_uuid", UUID(as_uuid=True), nullable=True))
    op.execute("UPDATE user_products SET id_uuid = uuid_generate_v4()")
    op.execute(
        """
        UPDATE user_products SET user_id_uuid = users.id_uuid
        FROM users WHERE user_products.user_id = users.id
    """
    )
    op.execute(
        """
        UPDATE user_products SET product_id_uuid = products.id_uuid
        FROM products WHERE user_products.product_id = products.id
    """
    )
    op.alter_column("user_products", "id_uuid", nullable=False)
    op.alter_column("user_products", "user_id_uuid", nullable=False)
    op.alter_column("user_products", "product_id_uuid", nullable=False)

    # Alerts table
    op.add_column("alerts", sa.Column("id_uuid", UUID(as_uuid=True), nullable=True))
    op.add_column("alerts", sa.Column("product_id_uuid", UUID(as_uuid=True), nullable=True))
    op.add_column("alerts", sa.Column("user_id_uuid", UUID(as_uuid=True), nullable=True))
    op.add_column("alerts", sa.Column("snapshot_id_uuid", UUID(as_uuid=True), nullable=True))
    op.execute("UPDATE alerts SET id_uuid = uuid_generate_v4()")
    op.execute(
        """
        UPDATE alerts SET product_id_uuid = products.id_uuid
        FROM products WHERE alerts.product_id = products.id
    """
    )
    op.execute(
        """
        UPDATE alerts SET user_id_uuid = users.id_uuid
        FROM users WHERE alerts.user_id = users.id
    """
    )
    op.execute(
        """
        UPDATE alerts SET snapshot_id_uuid = product_snapshots.id_uuid
        FROM product_snapshots WHERE alerts.snapshot_id = product_snapshots.id AND alerts.snapshot_id IS NOT NULL
    """
    )
    op.alter_column("alerts", "id_uuid", nullable=False)
    op.alter_column("alerts", "product_id_uuid", nullable=False)
    op.alter_column("alerts", "user_id_uuid", nullable=False)

    # Notifications table
    op.add_column("notifications", sa.Column("id_uuid", UUID(as_uuid=True), nullable=True))
    op.add_column("notifications", sa.Column("user_id_uuid", UUID(as_uuid=True), nullable=True))
    op.add_column("notifications", sa.Column("product_id_uuid", UUID(as_uuid=True), nullable=True))
    op.execute("UPDATE notifications SET id_uuid = uuid_generate_v4()")
    op.execute(
        """
        UPDATE notifications SET user_id_uuid = users.id_uuid
        FROM users WHERE notifications.user_id = users.id
    """
    )
    op.execute(
        """
        UPDATE notifications SET product_id_uuid = products.id_uuid
        FROM products WHERE notifications.product_id = products.id AND notifications.product_id IS NOT NULL
    """
    )
    op.alter_column("notifications", "id_uuid", nullable=False)
    op.alter_column("notifications", "user_id_uuid", nullable=False)

    # Suggestions table
    op.add_column("suggestions", sa.Column("id_uuid", UUID(as_uuid=True), nullable=True))
    op.add_column("suggestions", sa.Column("product_id_uuid", UUID(as_uuid=True), nullable=True))
    op.execute("UPDATE suggestions SET id_uuid = uuid_generate_v4()")
    op.execute(
        """
        UPDATE suggestions SET product_id_uuid = products.id_uuid
        FROM products WHERE suggestions.product_id = products.id AND suggestions.product_id IS NOT NULL
    """
    )
    op.alter_column("suggestions", "id_uuid", nullable=False)

    # Suggestion Actions table
    op.add_column("suggestion_actions", sa.Column("id_uuid", UUID(as_uuid=True), nullable=True))
    op.add_column(
        "suggestion_actions",
        sa.Column("suggestion_id_uuid", UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "suggestion_actions",
        sa.Column("reviewed_by_id_uuid", UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "suggestion_actions",
        sa.Column("applied_by_id_uuid", UUID(as_uuid=True), nullable=True),
    )
    op.execute("UPDATE suggestion_actions SET id_uuid = uuid_generate_v4()")
    op.execute(
        """
        UPDATE suggestion_actions SET suggestion_id_uuid = suggestions.id_uuid
        FROM suggestions WHERE suggestion_actions.suggestion_id = suggestions.id
    """
    )
    op.execute(
        """
        UPDATE suggestion_actions SET reviewed_by_id_uuid = users.id_uuid
        FROM users WHERE suggestion_actions.reviewed_by_id = users.id AND suggestion_actions.reviewed_by_id IS NOT NULL
    """
    )
    op.execute(
        """
        UPDATE suggestion_actions SET applied_by_id_uuid = users.id_uuid
        FROM users WHERE suggestion_actions.applied_by_id = users.id AND suggestion_actions.applied_by_id IS NOT NULL
    """
    )
    op.alter_column("suggestion_actions", "id_uuid", nullable=False)
    op.alter_column("suggestion_actions", "suggestion_id_uuid", nullable=False)

    # Step 2: Drop foreign key constraints and indexes that reference old integer IDs
    # Note: This list may need to be adjusted based on actual constraint names in your DB
    try:
        op.drop_constraint("user_settings_user_id_fkey", "user_settings", type_="foreignkey")
        op.drop_constraint("products_created_by_id_fkey", "products", type_="foreignkey")
        op.drop_constraint(
            "product_snapshots_product_id_fkey", "product_snapshots", type_="foreignkey"
        )
        op.drop_constraint("user_products_user_id_fkey", "user_products", type_="foreignkey")
        op.drop_constraint("user_products_product_id_fkey", "user_products", type_="foreignkey")
        op.drop_constraint("alerts_product_id_fkey", "alerts", type_="foreignkey")
        op.drop_constraint("alerts_user_id_fkey", "alerts", type_="foreignkey")
        op.drop_constraint("alerts_snapshot_id_fkey", "alerts", type_="foreignkey")
        op.drop_constraint("notifications_user_id_fkey", "notifications", type_="foreignkey")
        op.drop_constraint("notifications_product_id_fkey", "notifications", type_="foreignkey")
        op.drop_constraint("suggestions_product_id_fkey", "suggestions", type_="foreignkey")
        op.drop_constraint(
            "suggestion_actions_suggestion_id_fkey",
            "suggestion_actions",
            type_="foreignkey",
        )
        op.drop_constraint(
            "suggestion_actions_reviewed_by_id_fkey",
            "suggestion_actions",
            type_="foreignkey",
        )
        op.drop_constraint(
            "suggestion_actions_applied_by_id_fkey",
            "suggestion_actions",
            type_="foreignkey",
        )
    except Exception:
        # Foreign key names might be different, continue anyway
        pass

    # Drop unique constraints
    try:
        op.drop_constraint("uq_user_product", "user_products", type_="unique")
        op.drop_constraint("user_settings_user_id_key", "user_settings", type_="unique")
    except Exception:
        pass

    # Step 3: Drop old integer ID columns
    op.drop_column("users", "id", cascade=True)
    op.drop_column("user_settings", "id")
    op.drop_column("user_settings", "user_id")
    op.drop_column("products", "id")
    op.drop_column("products", "created_by_id")
    op.drop_column("product_snapshots", "id")
    op.drop_column("product_snapshots", "product_id")
    op.drop_column("user_products", "id")
    op.drop_column("user_products", "user_id")
    op.drop_column("user_products", "product_id")
    op.drop_column("alerts", "id")
    op.drop_column("alerts", "product_id")
    op.drop_column("alerts", "user_id")
    op.drop_column("alerts", "snapshot_id")
    op.drop_column("notifications", "id")
    op.drop_column("notifications", "user_id")
    op.drop_column("notifications", "product_id")
    op.drop_column("suggestions", "id")
    op.drop_column("suggestions", "product_id")
    op.drop_column("suggestion_actions", "id")
    op.drop_column("suggestion_actions", "suggestion_id")
    op.drop_column("suggestion_actions", "reviewed_by_id")
    op.drop_column("suggestion_actions", "applied_by_id")

    # Step 4: Rename UUID columns to 'id'
    op.alter_column("users", "id_uuid", new_column_name="id")
    op.alter_column("user_settings", "id_uuid", new_column_name="id")
    op.alter_column("user_settings", "user_id_uuid", new_column_name="user_id")
    op.alter_column("products", "id_uuid", new_column_name="id")
    op.alter_column("products", "created_by_id_uuid", new_column_name="created_by_id")
    op.alter_column("product_snapshots", "id_uuid", new_column_name="id")
    op.alter_column("product_snapshots", "product_id_uuid", new_column_name="product_id")
    op.alter_column("user_products", "id_uuid", new_column_name="id")
    op.alter_column("user_products", "user_id_uuid", new_column_name="user_id")
    op.alter_column("user_products", "product_id_uuid", new_column_name="product_id")
    op.alter_column("alerts", "id_uuid", new_column_name="id")
    op.alter_column("alerts", "product_id_uuid", new_column_name="product_id")
    op.alter_column("alerts", "user_id_uuid", new_column_name="user_id")
    op.alter_column("alerts", "snapshot_id_uuid", new_column_name="snapshot_id")
    op.alter_column("notifications", "id_uuid", new_column_name="id")
    op.alter_column("notifications", "user_id_uuid", new_column_name="user_id")
    op.alter_column("notifications", "product_id_uuid", new_column_name="product_id")
    op.alter_column("suggestions", "id_uuid", new_column_name="id")
    op.alter_column("suggestions", "product_id_uuid", new_column_name="product_id")
    op.alter_column("suggestion_actions", "id_uuid", new_column_name="id")
    op.alter_column("suggestion_actions", "suggestion_id_uuid", new_column_name="suggestion_id")
    op.alter_column("suggestion_actions", "reviewed_by_id_uuid", new_column_name="reviewed_by_id")
    op.alter_column("suggestion_actions", "applied_by_id_uuid", new_column_name="applied_by_id")

    # Step 5: Recreate primary key constraints
    op.create_primary_key("users_pkey", "users", ["id"])
    op.create_primary_key("user_settings_pkey", "user_settings", ["id"])
    op.create_primary_key("products_pkey", "products", ["id"])
    op.create_primary_key("product_snapshots_pkey", "product_snapshots", ["id"])
    op.create_primary_key("user_products_pkey", "user_products", ["id"])
    op.create_primary_key("alerts_pkey", "alerts", ["id"])
    op.create_primary_key("notifications_pkey", "notifications", ["id"])
    op.create_primary_key("suggestions_pkey", "suggestions", ["id"])
    op.create_primary_key("suggestion_actions_pkey", "suggestion_actions", ["id"])

    # Step 6: Recreate foreign key constraints
    op.create_foreign_key(
        "user_settings_user_id_fkey",
        "user_settings",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "products_created_by_id_fkey",
        "products",
        "users",
        ["created_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "product_snapshots_product_id_fkey",
        "product_snapshots",
        "products",
        ["product_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "user_products_user_id_fkey",
        "user_products",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "user_products_product_id_fkey",
        "user_products",
        "products",
        ["product_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "alerts_product_id_fkey",
        "alerts",
        "products",
        ["product_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "alerts_user_id_fkey",
        "alerts",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "alerts_snapshot_id_fkey",
        "alerts",
        "product_snapshots",
        ["snapshot_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "notifications_user_id_fkey",
        "notifications",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "notifications_product_id_fkey",
        "notifications",
        "products",
        ["product_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "suggestions_product_id_fkey",
        "suggestions",
        "products",
        ["product_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "suggestion_actions_suggestion_id_fkey",
        "suggestion_actions",
        "suggestions",
        ["suggestion_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "suggestion_actions_reviewed_by_id_fkey",
        "suggestion_actions",
        "users",
        ["reviewed_by_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "suggestion_actions_applied_by_id_fkey",
        "suggestion_actions",
        "users",
        ["applied_by_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Step 7: Recreate unique constraints and indexes
    op.create_unique_constraint("user_settings_user_id_key", "user_settings", ["user_id"])
    op.create_unique_constraint("uq_user_product", "user_products", ["user_id", "product_id"])

    # Recreate important indexes
    op.create_index("idx_products_created_by", "products", ["created_by_id"])
    op.create_index("idx_snapshot_product_id", "product_snapshots", ["product_id"])
    op.create_index("idx_user_products_user_id", "user_products", ["user_id"])
    op.create_index("idx_user_products_product_id", "user_products", ["product_id"])


def downgrade() -> None:
    """Downgrade schema - WARNING: This is destructive and will lose data."""
    # This downgrade is extremely complex and destructive
    # We won't implement it as UUID->INT conversion loses data
    raise NotImplementedError(
        "Downgrading from UUID to integer IDs is not supported as it's destructive. "
        "Restore from backup if you need to revert this migration."
    )
