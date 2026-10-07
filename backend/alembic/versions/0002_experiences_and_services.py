"""experiences and services

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-08 00:11:39.101613

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "experiences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("host_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "category",
            sa.Enum(
                "food",
                "heritage",
                "adventure",
                "wellness",
                "nature",
                "arts",
                name="experience_category",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("city", sa.String(length=80), nullable=False),
        sa.Column("state", sa.String(length=80), nullable=False),
        sa.Column("latitude", sa.Double(), nullable=False),
        sa.Column("longitude", sa.Double(), nullable=False),
        sa.Column("start_time", sa.String(length=5), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("price_per_guest", sa.Integer(), nullable=False),
        sa.Column("max_guests", sa.Integer(), nullable=False),
        sa.Column("rating_avg", sa.Double(), nullable=True),
        sa.Column("review_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "status",
            sa.Enum("draft", "active", "inactive", name="experience_status", native_enum=False),
            server_default="active",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "category IN ('food', 'heritage', 'adventure', 'wellness', 'nature', 'arts')",
            name=op.f("ck_experiences_experience_category"),
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'active', 'inactive')",
            name=op.f("ck_experiences_experience_status"),
        ),
        sa.CheckConstraint("duration_minutes > 0", name=op.f("ck_experiences_duration_positive")),
        sa.CheckConstraint("max_guests > 0", name=op.f("ck_experiences_max_guests_positive")),
        sa.CheckConstraint("price_per_guest > 0", name=op.f("ck_experiences_price_positive")),
        sa.CheckConstraint(
            "rating_avg IS NULL OR rating_avg BETWEEN 1 AND 5",
            name=op.f("ck_experiences_rating_range"),
        ),
        sa.ForeignKeyConstraint(
            ["host_id"],
            ["users.id"],
            name=op.f("fk_experiences_host_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_experiences")),
    )
    with op.batch_alter_table("experiences", schema=None) as batch_op:
        batch_op.create_index("ix_experiences_category", ["category"], unique=False)
        batch_op.create_index("ix_experiences_status_city", ["status", "city"], unique=False)

    op.create_table(
        "services",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("host_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "service_type",
            sa.Enum(
                "photography",
                "chefs",
                "training",
                "makeup",
                "hair",
                "massage",
                name="service_type",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("city", sa.String(length=80), nullable=False),
        sa.Column("state", sa.String(length=80), nullable=False),
        sa.Column("price_from", sa.Integer(), nullable=False),
        sa.Column("price_unit", sa.String(length=20), nullable=False),
        sa.Column("is_popular", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("rating_avg", sa.Double(), nullable=True),
        sa.Column("review_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "status",
            sa.Enum("draft", "active", "inactive", name="service_status", native_enum=False),
            server_default="active",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "service_type IN ('photography', 'chefs', 'training', 'makeup', 'hair', 'massage')",
            name=op.f("ck_services_service_type"),
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'active', 'inactive')", name=op.f("ck_services_service_status")
        ),
        sa.CheckConstraint("price_from > 0", name=op.f("ck_services_price_positive")),
        sa.CheckConstraint(
            "rating_avg IS NULL OR rating_avg BETWEEN 1 AND 5",
            name=op.f("ck_services_rating_range"),
        ),
        sa.ForeignKeyConstraint(
            ["host_id"], ["users.id"], name=op.f("fk_services_host_id_users"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_services")),
    )
    with op.batch_alter_table("services", schema=None) as batch_op:
        batch_op.create_index("ix_services_status_city", ["status", "city"], unique=False)
        batch_op.create_index("ix_services_type", ["service_type"], unique=False)

    op.create_table(
        "experience_photos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("experience_id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("card_url", sa.String(length=500), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["experience_id"],
            ["experiences.id"],
            name=op.f("fk_experience_photos_experience_id_experiences"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_experience_photos")),
        sa.UniqueConstraint(
            "experience_id", "position", name="uq_experience_photos_experience_id_position"
        ),
    )
    op.create_table(
        "service_photos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("service_id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("card_url", sa.String(length=500), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["service_id"],
            ["services.id"],
            name=op.f("fk_service_photos_service_id_services"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_service_photos")),
        sa.UniqueConstraint("service_id", "position", name="uq_service_photos_service_id_position"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("service_photos")
    op.drop_table("experience_photos")
    with op.batch_alter_table("services", schema=None) as batch_op:
        batch_op.drop_index("ix_services_type")
        batch_op.drop_index("ix_services_status_city")

    op.drop_table("services")
    with op.batch_alter_table("experiences", schema=None) as batch_op:
        batch_op.drop_index("ix_experiences_status_city")
        batch_op.drop_index("ix_experiences_category")

    op.drop_table("experiences")
