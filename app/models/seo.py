import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SeoScore(Base):
    __tablename__ = "seo_scores"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    listing_copy_id: Mapped[str] = mapped_column(ForeignKey("listing_copies.id", ondelete="CASCADE"))
    overall_score: Mapped[int] = mapped_column(Integer, default=0)
    checks: Mapped[str | None] = mapped_column(Text, nullable=True)
    scored_at: Mapped[str] = mapped_column(Text, default=lambda: datetime.now(timezone.utc).isoformat())
