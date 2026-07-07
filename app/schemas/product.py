from pydantic import BaseModel


class VariantCreate(BaseModel):
    option_name: str
    option_value: str
    sku: str | None = None
    barcode: str | None = None
    price: float | None = None
    cost_price: float | None = None
    inventory_qty: int = 0
    weight_grams: int | None = None


class ProductCreate(BaseModel):
    title: str
    category: str | None = None
    target_market: str | None = None
    supplier_name: str | None = None
    supplier_url: str | None = None
    cost_price: float | None = None
    target_price: float | None = None
    currency: str = "USD"
    notes: str | None = None
    variants: list[VariantCreate] | None = None


class ProductUpdate(BaseModel):
    title: str | None = None
    category: str | None = None
    target_market: str | None = None
    supplier_name: str | None = None
    supplier_url: str | None = None
    cost_price: float | None = None
    target_price: float | None = None
    currency: str | None = None
    notes: str | None = None


class VariantResponse(BaseModel):
    id: str
    option_name: str
    option_value: str
    sku: str | None
    barcode: str | None
    price: float | None
    cost_price: float | None
    inventory_qty: int
    weight_grams: int | None

    model_config = {"from_attributes": True}


class ImageResponse(BaseModel):
    id: str
    file_path: str
    alt_text: str | None
    position: int

    model_config = {"from_attributes": True}


class ProductResponse(BaseModel):
    id: str
    status: str
    title: str
    category: str | None
    target_market: str | None
    supplier_name: str | None
    supplier_url: str | None
    cost_price: float | None
    target_price: float | None
    currency: str
    notes: str | None
    shopify_gid: str | None
    shopify_handle: str | None
    created_at: str
    updated_at: str
    variants: list[VariantResponse] = []
    images: list[ImageResponse] = []

    model_config = {"from_attributes": True}
