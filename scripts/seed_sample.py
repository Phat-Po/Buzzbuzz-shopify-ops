"""Seed the database with sample product candidates for testing."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal, create_tables
from app.models.product import Product, ProductVariant, ProductImage, ProductStatus


SAMPLES = [
    {
        "title": "Bamboo Cutting Board Set (3 Sizes)",
        "category": "Kitchen",
        "target_market": "US",
        "supplier_name": "Yiwu Bamboo Co.",
        "cost_price": 4.50,
        "target_price": 24.99,
        "notes": "Organic bamboo. Available in S/M/L. Anti-slip silicone feet. Juice grooves on both sides. BPA-free.",
        "variants": [
            {"option_name": "Size", "option_value": "Small", "sku": "BCB-SM", "price": 14.99},
            {"option_name": "Size", "option_value": "Medium", "sku": "BCB-MD", "price": 19.99},
            {"option_name": "Size", "option_value": "Large", "sku": "BCB-LG", "price": 24.99},
        ],
    },
    {
        "title": "Portable LED Desk Lamp (USB-C Rechargeable)",
        "category": "Home Office",
        "target_market": "US",
        "supplier_name": "Shenzhen LightTech",
        "cost_price": 8.20,
        "target_price": 34.99,
        "notes": "3 color temperatures (warm/neutral/cool). 5 brightness levels. 4000mAh battery. Touch controls. Foldable arm.",
        "variants": [
            {"option_name": "Color", "option_value": "White", "sku": "LED-WH", "price": 34.99},
            {"option_name": "Color", "option_value": "Black", "sku": "LED-BK", "price": 34.99},
        ],
    },
    {
        "title": "Silicone Kitchen Utensil Set (12-Piece)",
        "category": "Kitchen",
        "target_market": "US",
        "supplier_name": "Dongguan Silicone Works",
        "cost_price": 6.80,
        "target_price": 29.99,
        "notes": "Heat resistant to 480F. Non-stick safe. Includes spatula, tongs, whisk, ladle, slotted spoon, etc. Stainless steel handles.",
    },
    {
        "title": "Minimalist Wallet (RFID Blocking)",
        "category": "Accessories",
        "target_market": "US",
        "supplier_name": "Guangzhou Leather Goods",
        "cost_price": 3.40,
        "target_price": 19.99,
        "notes": "Vegan leather. Holds 6 cards + cash. RFID blocking layer. Available in black, brown, navy.",
        "variants": [
            {"option_name": "Color", "option_value": "Black", "sku": "MW-BK", "price": 19.99},
            {"option_name": "Color", "option_value": "Brown", "sku": "MW-BR", "price": 19.99},
            {"option_name": "Color", "option_value": "Navy", "sku": "MW-NV", "price": 19.99},
        ],
    },
    {
        "title": "Resistance Band Set (5 Levels)",
        "category": "Fitness",
        "target_market": "Global",
        "cost_price": 2.10,
        "target_price": 15.99,
        "notes": "Natural latex. 5 resistance levels (X-Light to X-Heavy). Includes carry pouch and exercise guide.",
    },
]


def seed():
    create_tables()
    db = SessionLocal()
    try:
        for s in SAMPLES:
            product = Product(
                title=s["title"],
                category=s.get("category"),
                target_market=s.get("target_market"),
                supplier_name=s.get("supplier_name"),
                cost_price=s.get("cost_price"),
                target_price=s.get("target_price"),
                notes=s.get("notes"),
                status=ProductStatus.IDEA.value,
            )
            for v in s.get("variants", []):
                product.variants.append(
                    ProductVariant(
                        option_name=v["option_name"],
                        option_value=v["option_value"],
                        sku=v.get("sku"),
                        price=v.get("price"),
                    )
                )
            db.add(product)
        db.commit()
        print(f"Seeded {len(SAMPLES)} sample products.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
