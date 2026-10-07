from pathlib import Path

import pytest
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import inspect

from alembic import command
from app.core.database import Base, build_engine

BACKEND_DIR = Path(__file__).resolve().parent.parent
TABLES = {
    "users",
    "refresh_tokens",
    "categories",
    "amenities",
    "listings",
    "listing_photos",
    "listing_amenities",
    "bookings",
    "reviews",
    "wishlists",
    "wishlist_items",
    "experiences",
    "experience_photos",
    "services",
    "service_photos",
}


@pytest.fixture
def migrated(tmp_path):
    url = f"sqlite:///{tmp_path / 'migrated.db'}"
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")
    engine = build_engine(url)
    yield cfg, engine
    engine.dispose()


def test_upgrade_head_creates_every_table(migrated):
    _, engine = migrated
    assert set(inspect(engine).get_table_names()) >= TABLES


def test_migrations_match_the_models(migrated):
    """If this fails, a model changed without a new Alembic revision."""
    _, engine = migrated
    with engine.connect() as conn:
        context = MigrationContext.configure(conn, opts={"compare_type": True})
        assert compare_metadata(context, Base.metadata) == []


def test_downgrade_to_base_removes_everything(migrated):
    cfg, engine = migrated
    command.downgrade(cfg, "base")
    assert TABLES.isdisjoint(inspect(engine).get_table_names())


def test_migrated_check_constraints_match_the_models(migrated, tmp_path):
    """Alembic does not diff CHECK constraints, so compare them directly: the migration must
    create exactly the named constraints the models declare, no missing and no duplicates."""
    _, migrated_engine = migrated
    model_engine = build_engine(f"sqlite:///{tmp_path / 'from_models.db'}")
    Base.metadata.create_all(model_engine)
    try:
        for table in sorted(TABLES):
            from_migration = inspect(migrated_engine).get_check_constraints(table)
            from_models = inspect(model_engine).get_check_constraints(table)
            names = [c["name"] for c in from_migration]
            assert len(names) == len(set(names)), f"duplicate CHECK constraints on {table}: {names}"
            assert sorted(names) == sorted(c["name"] for c in from_models), table
    finally:
        model_engine.dispose()
