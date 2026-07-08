#!/usr/bin/env python3
"""BuzzBuzz: 推送產品到 Shopify

用法:
  python scripts/push.py products/<product-dir>

讀取 product.yaml → 透過 Shopify Admin GraphQL API 建立/更新產品
→ 所有產品預設建立為 DRAFT → 寫回 published 記錄到 product.yaml
"""

from __future__ import annotations

import sys
import json
import shutil
from pathlib import Path
from datetime import datetime, timezone

import yaml
import httpx
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    shopify_store: str = ""
    shopify_admin_token: str = ""
    shopify_api_version: str = "2026-04"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


def load_product(product_dir: Path) -> dict:
    """讀取產品 YAML 檔案"""
    yaml_path = product_dir / "product.yaml"
    if not yaml_path.exists():
        sys.exit(f"❌ 找不到 {yaml_path}")
    return yaml.safe_load(yaml_path.read_text(encoding="utf-8"))


def save_product(product_dir: Path, data: dict) -> None:
    """寫回產品 YAML 檔案（更新 published 記錄）"""
    yaml_path = product_dir / "product.yaml"
    yaml_path.write_text(yaml.dump(data, allow_unicode=True, default_flow_style=False), encoding="utf-8")


def build_product_input(data: dict) -> dict:
    """從 product.yaml 建立 Shopify GraphQL productInput"""
    title = data.get("title_zh") or data.get("product_name") or "未命名商品"
    desc_parts = []
    if data.get("description_fact"):
        desc_parts.append(data["description_fact"])
    if data.get("description_feel"):
        desc_parts.append(data["description_feel"])
    if data.get("description_trust"):
        desc_parts.append(data["description_trust"])
    description_html = "<br><br>".join(desc_parts) if desc_parts else ""

    product_type = data.get("product_type") or ""
    vendor = data.get("brand_en") or data.get("brand_jp") or ""

    tags = data.get("tags", [])
    if isinstance(tags, list):
        tags_str = ", ".join(tags)
    else:
        tags_str = str(tags)

    input_data = {
        "title": title,
        "descriptionHtml": description_html,
        "productType": product_type,
        "vendor": vendor,
        "tags": tags_str,
        "status": "DRAFT",
    }

    # SEO fields
    seo = {}
    if data.get("seo_title"):
        seo["title"] = data["seo_title"]
    if data.get("seo_meta"):
        seo["description"] = data["seo_meta"]
    if seo:
        input_data["seo"] = seo

    return input_data


def build_metafields_input(product_gid: str, data: dict) -> list[dict]:
    """建立 metafields 陣列"""
    metafields = []

    def add_metafield(key: str, value, type_: str = "single_line_text_field"):
        if value is not None and value != "":
            metafields.append({
                "ownerId": product_gid,
                "namespace": "buzzbuzz",
                "key": key,
                "value": str(value) if not isinstance(value, (bool, int, float)) else str(value).lower() if isinstance(value, bool) else str(value),
                "type": "single_line_text_field" if type_ not in ["number_integer", "number_decimal", "boolean", "json", "multi_line_text_field"] else type_,
            })

    # Map YAML fields to metafields (correct type per field)
    text_fields = {
        "brand_jp", "brand_en", "material", "dimensions",
        "price_gap_note", "country_of_origin", "season", "gender",
        "stock_status", "sourcing_status",
    }
    for k in text_fields:
        v = data.get(k)
        if v:
            add_metafield(k, v, "single_line_text_field")

    # Numeric fields
    for k in ("cost_jpy", "price_twd", "price_tw_ref", "weight_g"):
        v = data.get(k)
        if v:
            add_metafield(k, v, "number_decimal" if k == "price_twd" else "number_integer")

    # Boolean
    if data.get("japan_exclusive"):
        add_metafield("japan_exclusive", "true", "boolean")

    # List fields
    style_tags = data.get("style_tags", [])
    if style_tags:
        add_metafield("style_tags", json.dumps(style_tags, ensure_ascii=False), "json")

    return metafields


def create_product(client: httpx.Client, settings: Settings, input_data: dict) -> dict:
    """呼叫 Shopify GraphQL API 建立產品"""
    mutation = """
    mutation createProduct($input: ProductInput!) {
      productCreate(input: $input) {
        product {
          id
          handle
          onlineStorePreviewUrl
          status
        }
        userErrors {
          field
          message
        }
      }
    }
    """

    variables = {
        "input": input_data,
    }

    url = f"https://{settings.shopify_store}/admin/api/{settings.shopify_api_version}/graphql.json"
    headers = {
        "X-Shopify-Access-Token": settings.shopify_admin_token,
        "Content-Type": "application/json",
    }

    resp = client.post(url, json={"query": mutation, "variables": variables}, headers=headers)
    resp.raise_for_status()
    body = resp.json()

    if "errors" in body:
        sys.exit(f"❌ GraphQL 錯誤: {json.dumps(body['errors'], indent=2, ensure_ascii=False)}")

    result = body["data"]["productCreate"]
    if result["userErrors"]:
        for err in result["userErrors"]:
            print(f"  ⚠️  {err['field']}: {err['message']}")
        sys.exit("❌ 產品建立失敗")

    return result["product"]


def set_metafields(client: httpx.Client, settings: Settings, product_gid: str, metafields: list[dict]) -> None:
    """批次寫入 metafields"""
    if not metafields:
        return

    # Set ownerId on all metafields
    for mf in metafields:
        mf["ownerId"] = product_gid

    mutation = """
    mutation setMetafields($metafields: [MetafieldsSetInput!]!) {
      metafieldsSet(metafields: $metafields) {
        metafields {
          id
          namespace
          key
        }
        userErrors {
          field
          message
        }
      }
    }
    """

    url = f"https://{settings.shopify_store}/admin/api/{settings.shopify_api_version}/graphql.json"
    headers = {
        "X-Shopify-Access-Token": settings.shopify_admin_token,
        "Content-Type": "application/json",
    }

    resp = client.post(url, json={"query": mutation, "variables": {"metafields": metafields}}, headers=headers)
    resp.raise_for_status()
    body = resp.json()

    if "errors" in body:
        print(f"  ⚠️  Metafields 寫入錯誤: {json.dumps(body['errors'], indent=2, ensure_ascii=False)}")
        return

    result = body["data"]["metafieldsSet"]
    if result["userErrors"]:
        for err in result["userErrors"]:
            print(f"  ⚠️  Metafield {err['field']}: {err['message']}")
    else:
        print(f"  ✅ Metafields 已寫入 ({len(result['metafields'])} 個)")


def push_product(product_dir: Path) -> None:
    """主流程：讀取 → 推送到 Shopify → 寫回記錄"""
    settings = Settings()

    if not settings.shopify_store or not settings.shopify_admin_token:
        sys.exit("❌ 請先設定 .env 檔案（SHOPIFY_STORE 和 SHOPIFY_ADMIN_TOKEN）")

    data = load_product(product_dir)
    product_name = data.get("product_name") or product_dir.name

    print(f"\n🚀 推送: {product_name}")

    # Check if already published
    published = data.get("published", {})
    existing_id = published.get("shopify_id")
    if existing_id:
        print(f"  ℹ️  已發布過 (Shopify ID: {existing_id})")
        print(f"  ℹ️  目前只支援建立新產品，如需更新請手動操作 Shopify 後台")
        return

    # Build input
    input_data = build_product_input(data)

    with httpx.Client(timeout=30) as client:
        # Create product
        shopify_product = create_product(client, settings, input_data)
        product_gid = shopify_product["id"]
        product_url = shopify_product.get("onlineStorePreviewUrl") or shopify_product.get("onlineStoreUrl") or ""

        print(f"  ✅ 產品已建立")
        print(f"  📦 Shopify ID: {product_gid}")
        print(f"  🔗 預覽連結: {product_url}")

        # Set metafields
        metafields = build_metafields_input(product_gid, data)
        if metafields:
            set_metafields(client, settings, product_gid, metafields)

    # Update published record
    data["published"] = {
        "shopify_id": product_gid,
        "shopify_url": product_url,
        "shopify_status": "draft",
        "published_at": datetime.now(timezone.utc).isoformat(),
    }
    data["status"] = "published"
    save_product(product_dir, data)
    print(f"  💾 發布記錄已寫回 product.yaml")
    print(f"  🎉 完成！\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("用法: python scripts/push.py products/<product-dir>")

    product_dir = Path(sys.argv[1])
    if not product_dir.is_dir():
        sys.exit(f"❌ 找不到目錄: {product_dir}")

    push_product(product_dir)
