from datetime import datetime

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.adapters.sql.models.mixins import now_column
from app.core.database import Base


class WishlistModel(Base):
    __tablename__ = "wishlists"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_wishlists_user_id_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = now_column()


class WishlistItemModel(Base):
    __tablename__ = "wishlist_items"

    wishlist_id: Mapped[int] = mapped_column(
        ForeignKey("wishlists.id", ondelete="CASCADE"), primary_key=True
    )
    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listings.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = now_column()
