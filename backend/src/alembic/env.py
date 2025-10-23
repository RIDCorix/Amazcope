"""Alembic environment configuration for SQLAlchemy.

Note: Uses synchronous engine for migrations (simpler and more reliable).
The application itself uses async SQLAlchemy for FastAPI endpoints.
"""

from logging.config import fileConfig

from sqlalchemy import pool

from alembic import context  # type: ignore[attr-defined]

# Import all SQLAlchemy models so Alembic can detect them
from alert.models import Alert  # noqa: F401

# Import your Base and all models
from core.config import settings
from core.database import Base
from products.models import (  # noqa: F401
    BestsellerSnapshot,
    Category,
    Product,
    ProductSnapshot,
    Review,
    UserProduct,
)
from users.models import User, UserSettings  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set SQLAlchemy URL from settings
config.set_main_option("sqlalchemy.url", settings.SYNC_DATABASE_URL)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    Note: We use synchronous engine for migrations even though
    the application uses async. This is simpler and works better
    with Alembic's migration system.
    """
    from sqlalchemy import engine_from_config

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
