import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ReadinessCheck(Base):
    __tablename__ = "readiness_checks"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    platform: Mapped[str] = mapped_column(Text)
    checks: Mapped[str | None] = mapped_column(Text, nullable=True)
    checked_at: Mapped[str] = mapped_column(Text, default=lambda: datetime.now(timezone.utc).isoformat())
