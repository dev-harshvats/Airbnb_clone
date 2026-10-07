"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-10-07 22:44:22.999706

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create every table, constraint and index."""
    op.create_table(
        "amenities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("icon_key", sa.String(length=40), nullable=False),
        sa.Column(
            "group",
            sa.Enum(
                "essentials",
                "features",
                "safety",
                "location",
                name="amenity_group",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.CheckConstraint(
            "\"group\" IN ('essentials', 'features', 'safety', 'location')",
            name=op.f("ck_amenities_amenity_group"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_amenities")),
        sa.UniqueConstraint("key", name=op.f("uq_amenities_key")),
    )
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=40), nullable=False),
        sa.Column("label", sa.String(length=60), nullable=False),
        sa.Column("icon_key", sa.String(length=40), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
        sa.UniqueConstraint("slug", name=op.f("uq_categories_slug")),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("password_hash", sa.String(length=100), nullable=False),
        sa.Column("first_name", sa.String(length=50), nullable=False),
        sa.Column("last_name", sa.String(length=50), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("bio", sa.String(length=500), nullable=True),
        sa.Column("is_host", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("is_superhost", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_table(
        "listings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("host_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("property_type", sa.String(length=40), nullable=False),
        sa.Column(
            "place_type",
            sa.Enum("entire", "private_room", "shared_room", name="place_type", native_enum=False),
            nullable=False,
        ),
        sa.Column("address_line", sa.String(length=200), nullable=False),
        sa.Column("city", sa.String(length=80), nullable=False),
        sa.Column("state", sa.String(length=80), nullable=False),
        sa.Column("country", sa.String(length=80), server_default="India", nullable=False),
        sa.Column("postal_code", sa.String(length=12), nullable=False),
        sa.Column("latitude", sa.Double(), nullable=False),
        sa.Column("longitude", sa.Double(), nullable=False),
        sa.Column("price_per_night", sa.Integer(), nullable=False),
        sa.Column("cleaning_fee", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("min_nights", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("max_nights", sa.Integer(), server_default=sa.text("(90)"), nullable=False),
        sa.Column("max_guests", sa.Integer(), nullable=False),
        sa.Column("bedrooms", sa.Integer(), nullable=False),
        sa.Column("beds", sa.Integer(), nullable=False),
        sa.Column("bathrooms", sa.Numeric(precision=3, scale=1, asdecimal=False), nullable=False),
        sa.Column("pets_allowed", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("house_rules", sa.Text(), server_default="", nullable=False),
        sa.Column("check_in_time", sa.String(length=5), server_default="15:00", nullable=False),
        sa.Column("check_out_time", sa.String(length=5), server_default="11:00", nullable=False),
        sa.Column(
            "status",
            sa.Enum("draft", "active", "inactive", name="listing_status", native_enum=False),
            server_default="draft",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "place_type IN ('entire', 'private_room', 'shared_room')",
            name=op.f("ck_listings_place_type"),
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'active', 'inactive')", name=op.f("ck_listings_listing_status")
        ),
        sa.CheckConstraint(
            "bedrooms >= 0 AND beds >= 0 AND bathrooms >= 0",
            name=op.f("ck_listings_rooms_non_negative"),
        ),
        sa.CheckConstraint("cleaning_fee >= 0", name=op.f("ck_listings_cleaning_fee_non_negative")),
        sa.CheckConstraint("latitude BETWEEN -90 AND 90", name=op.f("ck_listings_latitude_range")),
        sa.CheckConstraint(
            "longitude BETWEEN -180 AND 180", name=op.f("ck_listings_longitude_range")
        ),
        sa.CheckConstraint("max_guests > 0", name=op.f("ck_listings_max_guests_positive")),
        sa.CheckConstraint(
            "max_nights >= min_nights", name=op.f("ck_listings_max_nights_not_below_min")
        ),
        sa.CheckConstraint("min_nights >= 1", name=op.f("ck_listings_min_nights_positive")),
        sa.CheckConstraint("price_per_night > 0", name=op.f("ck_listings_price_positive")),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name=op.f("fk_listings_category_id_categories"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["host_id"], ["users.id"], name=op.f("fk_listings_host_id_users"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_listings")),
    )
    with op.batch_alter_table("listings", schema=None) as batch_op:
        batch_op.create_index("ix_listings_category_id", ["category_id"], unique=False)
        batch_op.create_index("ix_listings_host_id", ["host_id"], unique=False)
        batch_op.create_index("ix_listings_price_per_night", ["price_per_night"], unique=False)
        batch_op.create_index("ix_listings_status_city", ["status", "city"], unique=False)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("family_id", sa.String(length=32), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("replaced_by_id", sa.Integer(), nullable=True),
        sa.Column("user_agent", sa.String(length=300), nullable=True),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["replaced_by_id"],
            ["refresh_tokens.id"],
            name=op.f("fk_refresh_tokens_replaced_by_id_refresh_tokens"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_refresh_tokens_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_refresh_tokens")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_refresh_tokens_token_hash")),
    )
    with op.batch_alter_table("refresh_tokens", schema=None) as batch_op:
        batch_op.create_index("ix_refresh_tokens_family_id", ["family_id"], unique=False)
        batch_op.create_index("ix_refresh_tokens_user_id", ["user_id"], unique=False)

    op.create_table(
        "wishlists",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_wishlists_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_wishlists")),
        sa.UniqueConstraint("user_id", "name", name="uq_wishlists_user_id_name"),
    )
    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=10), nullable=False),
        sa.Column("listing_id", sa.Integer(), nullable=False),
        sa.Column("guest_id", sa.Integer(), nullable=False),
        sa.Column("check_in", sa.Date(), nullable=False),
        sa.Column("check_out", sa.Date(), nullable=False),
        sa.Column("adults", sa.Integer(), nullable=False),
        sa.Column("children", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("infants", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("pets", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("nightly_rate", sa.Integer(), nullable=False),
        sa.Column("nights", sa.Integer(), nullable=False),
        sa.Column("subtotal", sa.Integer(), nullable=False),
        sa.Column("cleaning_fee", sa.Integer(), nullable=False),
        sa.Column("service_fee", sa.Integer(), nullable=False),
        sa.Column("taxes", sa.Integer(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("confirmed", "cancelled", name="booking_status", native_enum=False),
            server_default="confirmed",
            nullable=False,
        ),
        sa.Column(
            "payment_method_mock",
            sa.Enum("card", "upi", name="payment_method", native_enum=False),
            nullable=False,
        ),
        sa.Column("idempotency_key", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "payment_method_mock IN ('card', 'upi')", name=op.f("ck_bookings_payment_method")
        ),
        sa.CheckConstraint(
            "status IN ('confirmed', 'cancelled')", name=op.f("ck_bookings_booking_status")
        ),
        sa.CheckConstraint("adults >= 1", name=op.f("ck_bookings_adults_positive")),
        sa.CheckConstraint("check_out > check_in", name=op.f("ck_bookings_dates_ordered")),
        sa.CheckConstraint(
            "children >= 0 AND infants >= 0 AND pets >= 0",
            name=op.f("ck_bookings_guests_non_negative"),
        ),
        sa.CheckConstraint(
            "nightly_rate > 0 AND subtotal >= 0 AND cleaning_fee >= 0 AND service_fee >= 0 AND taxes >= 0 AND total >= 0",
            name=op.f("ck_bookings_amounts_valid"),
        ),
        sa.CheckConstraint("nights > 0", name=op.f("ck_bookings_nights_positive")),
        sa.ForeignKeyConstraint(
            ["guest_id"], ["users.id"], name=op.f("fk_bookings_guest_id_users"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["listing_id"],
            ["listings.id"],
            name=op.f("fk_bookings_listing_id_listings"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_bookings")),
        sa.UniqueConstraint("code", name=op.f("uq_bookings_code")),
        sa.UniqueConstraint(
            "guest_id", "idempotency_key", name="uq_bookings_guest_id_idempotency_key"
        ),
    )
    with op.batch_alter_table("bookings", schema=None) as batch_op:
        batch_op.create_index(
            "ix_bookings_availability",
            ["listing_id", "status", "check_in", "check_out"],
            unique=False,
        )
        batch_op.create_index("ix_bookings_guest_id", ["guest_id"], unique=False)

    op.create_table(
        "listing_amenities",
        sa.Column("listing_id", sa.Integer(), nullable=False),
        sa.Column("amenity_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["amenity_id"],
            ["amenities.id"],
            name=op.f("fk_listing_amenities_amenity_id_amenities"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["listing_id"],
            ["listings.id"],
            name=op.f("fk_listing_amenities_listing_id_listings"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("listing_id", "amenity_id", name=op.f("pk_listing_amenities")),
    )
    op.create_table(
        "listing_photos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("listing_id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("card_url", sa.String(length=500), nullable=False),
        sa.Column("caption", sa.String(length=200), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["listing_id"],
            ["listings.id"],
            name=op.f("fk_listing_photos_listing_id_listings"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_listing_photos")),
        sa.UniqueConstraint("listing_id", "position", name="uq_listing_photos_listing_id_position"),
    )
    op.create_table(
        "wishlist_items",
        sa.Column("wishlist_id", sa.Integer(), nullable=False),
        sa.Column("listing_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["listing_id"],
            ["listings.id"],
            name=op.f("fk_wishlist_items_listing_id_listings"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["wishlist_id"],
            ["wishlists.id"],
            name=op.f("fk_wishlist_items_wishlist_id_wishlists"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("wishlist_id", "listing_id", name=op.f("pk_wishlist_items")),
    )
    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("booking_id", sa.Integer(), nullable=False),
        sa.Column("listing_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("cleanliness", sa.Integer(), nullable=False),
        sa.Column("accuracy", sa.Integer(), nullable=False),
        sa.Column("check_in", sa.Integer(), nullable=False),
        sa.Column("communication", sa.Integer(), nullable=False),
        sa.Column("location", sa.Integer(), nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column("comment", sa.String(length=2000), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "rating BETWEEN 1 AND 5 AND cleanliness BETWEEN 1 AND 5 AND accuracy BETWEEN 1 AND 5 AND check_in BETWEEN 1 AND 5 AND communication BETWEEN 1 AND 5 AND location BETWEEN 1 AND 5 AND value BETWEEN 1 AND 5",
            name=op.f("ck_reviews_ratings_in_range"),
        ),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["users.id"],
            name=op.f("fk_reviews_author_id_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["booking_id"],
            ["bookings.id"],
            name=op.f("fk_reviews_booking_id_bookings"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["listing_id"],
            ["listings.id"],
            name=op.f("fk_reviews_listing_id_listings"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reviews")),
        sa.UniqueConstraint("booking_id", name=op.f("uq_reviews_booking_id")),
    )
    with op.batch_alter_table("reviews", schema=None) as batch_op:
        batch_op.create_index("ix_reviews_listing_id", ["listing_id"], unique=False)


def downgrade() -> None:
    """Drop everything created by upgrade()."""
    with op.batch_alter_table("reviews", schema=None) as batch_op:
        batch_op.drop_index("ix_reviews_listing_id")

    op.drop_table("reviews")
    op.drop_table("wishlist_items")
    op.drop_table("listing_photos")
    op.drop_table("listing_amenities")
    with op.batch_alter_table("bookings", schema=None) as batch_op:
        batch_op.drop_index("ix_bookings_guest_id")
        batch_op.drop_index("ix_bookings_availability")

    op.drop_table("bookings")
    op.drop_table("wishlists")
    with op.batch_alter_table("refresh_tokens", schema=None) as batch_op:
        batch_op.drop_index("ix_refresh_tokens_user_id")
        batch_op.drop_index("ix_refresh_tokens_family_id")

    op.drop_table("refresh_tokens")
    with op.batch_alter_table("listings", schema=None) as batch_op:
        batch_op.drop_index("ix_listings_status_city")
        batch_op.drop_index("ix_listings_price_per_night")
        batch_op.drop_index("ix_listings_host_id")
        batch_op.drop_index("ix_listings_category_id")

    op.drop_table("listings")
    op.drop_table("users")
    op.drop_table("categories")
    op.drop_table("amenities")
