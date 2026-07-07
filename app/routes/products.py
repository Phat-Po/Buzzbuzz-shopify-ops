import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import MEDIA_DIR
from app.database import get_db
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services import product_service
from app.services.importer import import_csv, import_json

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=list[ProductResponse])
def list_products(status: str | None = None, db: Session = Depends(get_db)):
    return product_service.list_products(db, status)


@router.post("", response_model=ProductResponse, status_code=201)
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    return product_service.create_product(db, data)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: str, db: Session = Depends(get_db)):
    product = product_service.get_product(db, product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product_id: str, data: ProductUpdate, db: Session = Depends(get_db)):
    product = product_service.update_product(db, product_id, data)
    if not product:
        raise HTTPException(404, "Product not found")
    return product


@router.delete("/{product_id}")
def delete_product(product_id: str, db: Session = Depends(get_db)):
    if not product_service.delete_product(db, product_id):
        raise HTTPException(404, "Product not found")
    return {"ok": True}


@router.post("/{product_id}/advance", response_model=ProductResponse)
def advance_status(product_id: str, db: Session = Depends(get_db)):
    product, error = product_service.advance_status(db, product_id)
    if error:
        raise HTTPException(400, error)
    return product


@router.post("/{product_id}/revert")
def revert_status(product_id: str, to_status: str, db: Session = Depends(get_db)):
    product, error = product_service.revert_status(db, product_id, to_status)
    if error:
        raise HTTPException(400, error)
    return ProductResponse.model_validate(product)


@router.post("/{product_id}/images")
def upload_image(product_id: str, file: UploadFile, alt_text: str | None = None, db: Session = Depends(get_db)):
    product = product_service.get_product(db, product_id)
    if not product:
        raise HTTPException(404, "Product not found")

    product_media_dir = MEDIA_DIR / product_id
    product_media_dir.mkdir(parents=True, exist_ok=True)
    dest = product_media_dir / file.filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    rel_path = f"{product_id}/{file.filename}"
    image = product_service.add_image(db, product_id, rel_path, alt_text)
    return {"id": image.id, "file_path": image.file_path, "position": image.position}


@router.delete("/images/{image_id}")
def delete_image(image_id: str, db: Session = Depends(get_db)):
    if not product_service.delete_image(db, image_id):
        raise HTTPException(404, "Image not found")
    return {"ok": True}


@router.post("/import")
def import_file(file: UploadFile, db: Session = Depends(get_db)):
    suffix = Path(file.filename).suffix.lower() if file.filename else ""
    if suffix not in (".csv", ".json"):
        raise HTTPException(400, "Only .csv and .json files are supported")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)

    try:
        if suffix == ".csv":
            products = import_csv(db, tmp_path)
        else:
            products = import_json(db, tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    return {"imported": len(products), "product_ids": [p.id for p in products]}


@router.post("/{product_id}/variants")
def add_variant(
    product_id: str,
    option_name: str,
    option_value: str,
    sku: str | None = None,
    price: float | None = None,
    db: Session = Depends(get_db),
):
    variant = product_service.add_variant(db, product_id, option_name, option_value, sku=sku, price=price)
    if not variant:
        raise HTTPException(404, "Product not found")
    return {"id": variant.id, "option_name": variant.option_name, "option_value": variant.option_value}


@router.delete("/variants/{variant_id}")
def delete_variant(variant_id: str, db: Session = Depends(get_db)):
    if not product_service.delete_variant(db, variant_id):
        raise HTTPException(404, "Variant not found")
    return {"ok": True}
