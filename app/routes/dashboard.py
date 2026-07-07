from fastapi import APIRouter, Depends, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import BASE_DIR, MEDIA_DIR
from app.database import get_db
from app.models.product import ADVANCE_GATES, PIPELINE_ORDER, ProductStatus
from app.schemas.product import ProductCreate, ProductUpdate
from app.services import product_service

import shutil

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))


def _render(request: Request, name: str, ctx: dict | None = None):
    return templates.TemplateResponse(request, name, ctx)


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    all_products = product_service.list_products(db)
    by_status: dict[str, list] = {}
    for s in PIPELINE_ORDER:
        by_status[s.value] = []
    for p in all_products:
        by_status.setdefault(p.status, []).append(p)
    return _render(request, "dashboard.html", {
        "by_status": by_status,
        "pipeline": PIPELINE_ORDER,
        "total": len(all_products),
    })


@router.get("/products/new", response_class=HTMLResponse)
def new_product_form(request: Request):
    return _render(request, "product_form.html", {"product": None})


@router.post("/products/new")
def create_product_form(
    request: Request,
    title: str = Form(...),
    category: str = Form(""),
    target_market: str = Form(""),
    supplier_name: str = Form(""),
    supplier_url: str = Form(""),
    cost_price: str = Form(""),
    target_price: str = Form(""),
    currency: str = Form("USD"),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    data = ProductCreate(
        title=title,
        category=category or None,
        target_market=target_market or None,
        supplier_name=supplier_name or None,
        supplier_url=supplier_url or None,
        cost_price=float(cost_price) if cost_price else None,
        target_price=float(target_price) if target_price else None,
        currency=currency,
        notes=notes or None,
    )
    product = product_service.create_product(db, data)
    return RedirectResponse(f"/products/{product.id}", status_code=303)


@router.get("/products/{product_id}", response_class=HTMLResponse)
def product_detail(request: Request, product_id: str, db: Session = Depends(get_db)):
    product = product_service.get_product(db, product_id)
    if not product:
        return HTMLResponse("<h1>Product not found</h1>", status_code=404)

    current_status = ProductStatus(product.status)
    current_idx = PIPELINE_ORDER.index(current_status)
    can_advance = current_idx < len(PIPELINE_ORDER) - 1

    missing = []
    if can_advance:
        next_status = PIPELINE_ORDER[current_idx + 1]
        gates = ADVANCE_GATES.get(next_status, [])
        for gate in gates:
            if gate == "_has_image" and not product.images:
                missing.append("At least one image")
            elif gate == "_has_notes" and not product.notes:
                missing.append("Product notes")
            elif not gate.startswith("_") and getattr(product, gate, None) is None:
                missing.append(gate.replace("_", " ").title())

    return _render(request, "product_detail.html", {
        "product": product,
        "pipeline": PIPELINE_ORDER,
        "current_idx": current_idx,
        "can_advance": can_advance,
        "missing": missing,
    })


@router.get("/products/{product_id}/edit", response_class=HTMLResponse)
def edit_product_form(request: Request, product_id: str, db: Session = Depends(get_db)):
    product = product_service.get_product(db, product_id)
    if not product:
        return HTMLResponse("<h1>Product not found</h1>", status_code=404)
    return _render(request, "product_form.html", {"product": product})


@router.post("/products/{product_id}/edit")
def update_product_form(
    product_id: str,
    title: str = Form(...),
    category: str = Form(""),
    target_market: str = Form(""),
    supplier_name: str = Form(""),
    supplier_url: str = Form(""),
    cost_price: str = Form(""),
    target_price: str = Form(""),
    currency: str = Form("USD"),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    data = ProductUpdate(
        title=title,
        category=category or None,
        target_market=target_market or None,
        supplier_name=supplier_name or None,
        supplier_url=supplier_url or None,
        cost_price=float(cost_price) if cost_price else None,
        target_price=float(target_price) if target_price else None,
        currency=currency,
        notes=notes or None,
    )
    product_service.update_product(db, product_id, data)
    return RedirectResponse(f"/products/{product_id}", status_code=303)


@router.post("/products/{product_id}/advance")
def advance_product(product_id: str, db: Session = Depends(get_db)):
    product, error = product_service.advance_status(db, product_id)
    if error:
        return RedirectResponse(f"/products/{product_id}?error={error}", status_code=303)
    return RedirectResponse(f"/products/{product_id}", status_code=303)


@router.post("/products/{product_id}/upload-image")
async def upload_image_form(product_id: str, file: UploadFile, db: Session = Depends(get_db)):
    product = product_service.get_product(db, product_id)
    if not product:
        return HTMLResponse("<h1>Product not found</h1>", status_code=404)

    product_media_dir = MEDIA_DIR / product_id
    product_media_dir.mkdir(parents=True, exist_ok=True)
    dest = product_media_dir / file.filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    rel_path = f"{product_id}/{file.filename}"
    product_service.add_image(db, product_id, rel_path)
    return RedirectResponse(f"/products/{product_id}", status_code=303)


@router.post("/products/{product_id}/delete")
def delete_product_form(product_id: str, db: Session = Depends(get_db)):
    product_service.delete_product(db, product_id)
    return RedirectResponse("/", status_code=303)


@router.get("/import", response_class=HTMLResponse)
def import_form(request: Request):
    return _render(request, "import.html", {})
