from sqlalchemy.orm import Session

from app.models.product import (
    ADVANCE_GATES,
    PIPELINE_ORDER,
    Product,
    ProductImage,
    ProductStatus,
    ProductVariant,
)
from app.schemas.product import ProductCreate, ProductUpdate


def create_product(db: Session, data: ProductCreate) -> Product:
    product = Product(
        title=data.title,
        category=data.category,
        target_market=data.target_market,
        supplier_name=data.supplier_name,
        supplier_url=data.supplier_url,
        cost_price=data.cost_price,
        target_price=data.target_price,
        currency=data.currency,
        notes=data.notes,
    )
    if data.variants:
        for v in data.variants:
            product.variants.append(
                ProductVariant(
                    option_name=v.option_name,
                    option_value=v.option_value,
                    sku=v.sku,
                    barcode=v.barcode,
                    price=v.price,
                    cost_price=v.cost_price,
                    inventory_qty=v.inventory_qty,
                    weight_grams=v.weight_grams,
                )
            )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def list_products(db: Session, status: str | None = None) -> list[Product]:
    q = db.query(Product)
    if status:
        q = q.filter(Product.status == status)
    return q.order_by(Product.updated_at.desc()).all()


def get_product(db: Session, product_id: str) -> Product | None:
    return db.query(Product).filter(Product.id == product_id).first()


def update_product(db: Session, product_id: str, data: ProductUpdate) -> Product | None:
    product = get_product(db, product_id)
    if not product:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: str) -> bool:
    product = get_product(db, product_id)
    if not product:
        return False
    db.delete(product)
    db.commit()
    return True


def _check_gate(product: Product, target_status: ProductStatus) -> str | None:
    gates = ADVANCE_GATES.get(target_status, [])
    for gate in gates:
        if gate == "_has_image":
            if not product.images:
                return "At least one image is required"
        elif gate == "_has_notes":
            if not product.notes:
                return "Product notes are required"
        else:
            val = getattr(product, gate, None)
            if val is None:
                return f"Field '{gate}' is required"
    return None


def advance_status(db: Session, product_id: str) -> tuple[Product | None, str | None]:
    product = get_product(db, product_id)
    if not product:
        return None, "Product not found"

    current = ProductStatus(product.status)
    idx = PIPELINE_ORDER.index(current)
    if idx >= len(PIPELINE_ORDER) - 1:
        return product, "Already at final status"

    next_status = PIPELINE_ORDER[idx + 1]
    error = _check_gate(product, next_status)
    if error:
        return product, error

    product.status = next_status.value
    db.commit()
    db.refresh(product)
    return product, None


def revert_status(db: Session, product_id: str, to_status: str) -> tuple[Product | None, str | None]:
    product = get_product(db, product_id)
    if not product:
        return None, "Product not found"

    try:
        target = ProductStatus(to_status)
    except ValueError:
        return product, f"Invalid status: {to_status}"

    current_idx = PIPELINE_ORDER.index(ProductStatus(product.status))
    target_idx = PIPELINE_ORDER.index(target)
    if target_idx >= current_idx:
        return product, "Can only revert to an earlier status"

    product.status = target.value
    db.commit()
    db.refresh(product)
    return product, None


def add_image(db: Session, product_id: str, file_path: str, alt_text: str | None = None) -> ProductImage | None:
    product = get_product(db, product_id)
    if not product:
        return None
    max_pos = max((img.position for img in product.images), default=-1)
    image = ProductImage(
        product_id=product_id,
        file_path=file_path,
        alt_text=alt_text,
        position=max_pos + 1,
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


def delete_image(db: Session, image_id: str) -> bool:
    image = db.query(ProductImage).filter(ProductImage.id == image_id).first()
    if not image:
        return False
    db.delete(image)
    db.commit()
    return True


def add_variant(db: Session, product_id: str, option_name: str, option_value: str, **kwargs) -> ProductVariant | None:
    product = get_product(db, product_id)
    if not product:
        return None
    variant = ProductVariant(
        product_id=product_id,
        option_name=option_name,
        option_value=option_value,
        **kwargs,
    )
    db.add(variant)
    db.commit()
    db.refresh(variant)
    return variant


def delete_variant(db: Session, variant_id: str) -> bool:
    variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    if not variant:
        return False
    db.delete(variant)
    db.commit()
    return True
