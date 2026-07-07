import csv
import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.product import Product, ProductVariant
from app.schemas.product import ProductCreate, VariantCreate


def _row_to_create(row: dict) -> ProductCreate:
    variants = []
    if row.get("variant_option") and row.get("variant_value"):
        variants.append(
            VariantCreate(
                option_name=row["variant_option"],
                option_value=row["variant_value"],
                sku=row.get("variant_sku"),
                price=float(row["variant_price"]) if row.get("variant_price") else None,
            )
        )
    return ProductCreate(
        title=row.get("title", "Untitled"),
        category=row.get("category"),
        target_market=row.get("target_market"),
        supplier_name=row.get("supplier_name"),
        supplier_url=row.get("supplier_url"),
        cost_price=float(row["cost_price"]) if row.get("cost_price") else None,
        target_price=float(row["target_price"]) if row.get("target_price") else None,
        currency=row.get("currency", "USD"),
        notes=row.get("notes"),
        variants=variants if variants else None,
    )


def import_csv(db: Session, file_path: Path) -> list[Product]:
    products = []
    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data = _row_to_create(row)
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
                source_data=json.dumps(row, ensure_ascii=False),
            )
            if data.variants:
                for v in data.variants:
                    product.variants.append(
                        ProductVariant(
                            option_name=v.option_name,
                            option_value=v.option_value,
                            sku=v.sku,
                            price=v.price,
                        )
                    )
            db.add(product)
            products.append(product)
    db.commit()
    return products


def import_json(db: Session, file_path: Path) -> list[Product]:
    with open(file_path, encoding="utf-8") as f:
        items = json.load(f)

    if isinstance(items, dict):
        items = [items]

    products = []
    for row in items:
        data = _row_to_create(row)
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
            source_data=json.dumps(row, ensure_ascii=False),
        )
        if data.variants:
            for v in data.variants:
                product.variants.append(
                    ProductVariant(
                        option_name=v.option_name,
                        option_value=v.option_value,
                        sku=v.sku,
                        price=v.price,
                    )
                )
        db.add(product)
        products.append(product)
    db.commit()
    return products
