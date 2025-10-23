"""add_denormalized_fields_to_product

Revision ID: f7b792cfde2a
Revises: 38e96f2fc953
Create Date: 2025-10-23 15:29:04.026252

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f7b792cfde2a"
down_revision: str | Sequence[str] | None = "38e96f2fc953"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add denormalized fields to products table
    op.add_column(
        "products",
        sa.Column(
            "current_price",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
            comment="Latest price from most recent snapshot",
        ),
    )
    op.add_column(
        "products",
    sa.Column(
            "original_price",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
            comment="Latest original price (before discount)",
        ),
    )
    op.add_column(
        "products",
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
            server_default="USD",
            comment="Currency code (USD, GBP, EUR, etc.)",
        ),
    )
    op.add_column(
        "products",
        sa.Column(
            "discount_percentage", sa.Float(), nullable=True, comment="Current discount percentage"
        ),
    )
    op.add_column(
        "products",
        sa.Column(
            "current_bsr",
            sa.Integer(),
            nullable=True,
            comment="Latest Best Seller Rank in main category",
        ),
    )
    op.add_column(
        "products",
        sa.Column(
            "bsr_category_name",
            sa.String(length=200),
            nullable=True,
            comment="BSR main category name",
        ),
    )
    op.add_column(
        "products",
        sa.Column(
            "in_stock",
            sa.Boolean(),
            nullable=False,
            server_default="true",
            comment="Whether product is currently in stock",
        ),
    )
    op.add_column(
        "products",
        sa.Column(
            "stock_status",
            sa.String(length=50),
            nullable=True,
            comment="Detailed stock status text",
        ),
    )
    op.add_column(
        "products",
        sa.Column(
            "is_prime",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="Whether Prime shipping is available",
        ),
    )
    op.add_column(
        "products",
        sa.Column(
            "seller_name", sa.String(length=255), nullable=True, comment="Current seller name"
        ),
    )
    op.add_column(
        "products",
        sa.Column(
            "is_amazon_seller",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="Whether sold by Amazon",
        ),
    )
    op.add_column(
        "products",
        sa.Column(
            "is_fba",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="Whether Fulfilled by Amazon (FBA)",
        ),
    )
    op.add_column(
        "products",
        sa.Column(
            "last_snapshot_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Timestamp of the last snapshot that updated these fields",
        ),
    )

    # Create performance indexes
    op.create_index("idx_products_current_price", "products", ["current_price"], unique=False)
    op.create_index("idx_products_current_bsr", "products", ["current_bsr"], unique=False)
    op.create_index("idx_products_in_stock", "products", ["in_stock"], unique=False)
    op.create_index("idx_products_is_prime", "products", ["is_prime"], unique=False)
    op.create_index("idx_products_last_snapshot_at", "products", ["last_snapshot_at"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index("idx_products_last_snapshot_at", table_name="products")
    op.drop_index("idx_products_is_prime", table_name="products")
    op.drop_index("idx_products_in_stock", table_name="products")
    op.drop_index("idx_products_current_bsr", table_name="products")
    op.drop_index("idx_products_current_price", table_name="products")

    # Drop columns
    op.drop_column("products", "last_snapshot_at")
    op.drop_column("products", "is_fba")
    op.drop_column("products", "is_amazon_seller")
    op.drop_column("products", "seller_name")
    op.drop_column("products", "is_prime")
    op.drop_column("products", "stock_status")
    op.drop_column("products", "in_stock")
    op.drop_column("products", "bsr_category_name")
    op.drop_column("products", "current_bsr")
    op.drop_column("products", "discount_percentage")
    op.drop_column("products", "currency")
    op.drop_column("products", "original_price")
    op.drop_column("products", "current_price")
