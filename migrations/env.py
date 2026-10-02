import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

import app.models  # noqa: F401  # registers all models on Base.metadata
from app.config import settings
from app.db import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# disable_existing_loggers=False: fileConfig() defaults to disabling every
# logger not explicitly listed in alembic.ini's [loggers] section. When
# migrations run inside the test suite (see tests/conftest.py), that would
# silently disable app.access and any other app logger that already exists.
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

# DATABASE_URL comes from app.config.settings (.env), not alembic.ini, so the
# connection string is defined in exactly one place. DATABASE_URL_OVERRIDE lets
# the test suite point this at dispensa_test instead (see tests/conftest.py);
# it's never set outside of that.
config.set_main_option(
    "sqlalchemy.url", os.environ.get("DATABASE_URL_OVERRIDE", settings.database_url)
)

# add your model's MetaData object here
# for 'autogenerate' support
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
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
