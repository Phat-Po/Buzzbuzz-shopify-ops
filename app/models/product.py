import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Enum, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProductStatus(str, enum.Enum):
    IDEA = "IDEA"
    SOURCED = "SOURCED"
    MATERIAL_READY = "MATERIAL_READY"
    AI_COPY_GENERATED = "AI_COPY_GENERATED"
    SEO_REVIEWED = "SEO_REVIEWED"
    READY_TO_PUBLISH = "READY_TO_PUBLISH"
    PUBLISHED_DRAFT = "PUBLISHED_DRAFT"
    LIVE = "LIVE"
    TRACKING = "TRACKING"


PIPELINE_ORDER = list(ProductStatus)

ADVANCE_GATES: dict[ProductStatus, list[str]] = {
    ProductStatus.SOURCED: ["cost_price"],
    ProductStatus.MATERIAL_READY: ["_has_image", "_has_notes"],
}


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uuid() -> str:
    return str(uuid.uuid4())


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=_uuid)
    status: Mapped[str] = mapped_column(Text, default=ProductStatus.IDEA.value)
    title: Mapped[str] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_market: Mapped[str | None] = mapped_column(Text, nullable=True)
    supplier_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    supplier_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    cost_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(Text, default="USD")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    shopify_gid: Mapped[str | None] = mapped_column(Text, nullable=True)
    shopify_handle: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(Text, default=_utcnow)
    updated_at: Mapped[str] = mapped_column(Text, default=_utcnow, onupdate=_utcnow)

    variants: Mapped[list["ProductVariant"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    images: Mapped[list["ProductImage"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", order_by="ProductImage.position"
    )


class ProductVariant(Base):
    __tablename__ = "product_variants"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=_uuid)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    option_name: Mapped[str] = mapped_column(Text)
    option_value: Mapped[str] = mapped_column(Text)
    sku: Mapped[str | None] = mapped_column(Text, nullable=True)
    barcode: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    inventory_qty: Mapped[int] = mapped_column(Integer, default=0)
    weight_grams: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shopify_variant_gid: Mapped[str | None] = mapped_column(Text, nullable=True)

    product: Mapped["Product"] = relationship(back_populates="variants")


class ProductImage(Base):
    __tablename__ = "product_images"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=_uuid)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    file_path: Mapped[str] = mapped_column(Text)
    alt_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    shopify_media_gid: Mapped[str | None] = mapped_column(Text, nullable=True)

    product: Mapped["Product"] = relationship(back_populates="images")
