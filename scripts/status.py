#!/usr/bin/env python3
"""BuzzBuzz: 查看所有產品狀態

用法:
  python scripts/status.py          列出所有產品
  python scripts/status.py --json   輸出 JSON 格式
"""

from __future__ import annotations

import sys
import json
from pathlib import Path
from datetime import datetime, timezone

import yaml


STATUS_EMOJI = {
    "draft": "✏️",
    "review": "👀",
    "ready": "✅",
    "published": "📦",
}


def scan_products(base_dir: Path) -> list[dict]:
    """掃描所有產品目錄，回傳產品狀態列表"""
    if not base_dir.is_dir():
        return []

    products = []
    for d in base_dir.iterdir():
        if not d.is_dir() or d.name.startswith("_"):
            continue

        yaml_path = d / "product.yaml"
        if not yaml_path.exists():
            products.append({
                "dir": d.name,
                "name": d.name,
                "status": "no_yaml",
                "shopify": "",
                "error": "缺少 product.yaml",
            })
            continue

        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        name = data.get("product_name") or data.get("brand_jp") or d.name
        status = data.get("status", "draft")
        published = data.get("published", {})
        shopify_status = published.get("shopify_status", "")
        shopify_id = published.get("shopify_id", "")

        if shopify_id:
            shopify_display = f"已發布 ({shopify_status or 'draft'})" if shopify_status else "已發布"
        else:
            shopify_display = "未發布"

        products.append({
            "dir": d.name,
            "name": name,
            "status": status,
            "shopify": shopify_display,
            "shopify_id": shopify_id,
            "shopify_url": published.get("shopify_url", ""),
            "brand_jp": data.get("brand_jp", ""),
            "brand_en": data.get("brand_en", ""),
            "product_type": data.get("product_type", ""),
            "price_twd": data.get("price_twd", 0),
        })

    return products


def print_table(products: list[dict]) -> None:
    """印出表格"""
    if not products:
        print("📭 尚無產品。在 products/ 下建立產品資料夾即可開始。")
        print("   參考: products/_template/product.yaml")
        return

    # Calculate column widths
    name_width = max(max(len(p["name"]) for p in products), 20)
    name_width = min(name_width, 40)  # cap

    print(f"\n{'產品名稱':<{name_width}}  狀態        Shopify")
    print(f"{'─'*name_width}  ─────────  ─────────────────")

    for p in products:
        emoji = STATUS_EMOJI.get(p["status"], "❓")
        name = p["name"][:name_width]
        status_display = f"{emoji} {p['status']:<8}"

        if p.get("error"):
            print(f"{name:<{name_width}}  {status_display}  ⚠️ {p['error']}")
        else:
            price = f"NT${p['price_twd']:,}" if p.get("price_twd") else ""
            shopify = p['shopify']
            print(f"{name:<{name_width}}  {status_display}  {shopify}  {price}")

    print()
    print(f"共 {len(products)} 個產品")
    print()


def main():
    base_dir = Path("products")
    products = scan_products(base_dir)

    if "--json" in sys.argv:
        print(json.dumps(products, ensure_ascii=False, indent=2))
        return

    print_table(products)


if __name__ == "__main__":
    main()
