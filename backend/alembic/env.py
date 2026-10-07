"""Alembic environment: the database URL comes from the app settings, the schema from the models."""

from alembic import context
from app.adapters.sql import models  # noqa: F401  (importing registers every table on the metadata)
from app.core.config import get_settings
from app.core.database import Base, build_engine

config = context.config
target_metadata = Base.metadata

# Tests (and tooling) may pass a URL through the config; otherwise use the app's setting.
DATABASE_URL = config.get_main_option("sqlalchemy.url") or get_settings().DATABASE_URL

# SQLite cannot ALTER most things in place, so Alembic rebuilds tables ("batch mode").
_CONTEXT_OPTIONS = {
    "target_metadata": target_metadata,
    "render_as_batch": True,
    "compare_type": True,
}


def run_migrations_offline() -> None:
    context.configure(url=DATABASE_URL, literal_binds=True, **_CONTEXT_OPTIONS)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = build_engine(DATABASE_URL)  # same pragmas (foreign keys, WAL) as the running app
    with engine.connect() as connection:
        context.configure(connection=connection, **_CONTEXT_OPTIONS)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
