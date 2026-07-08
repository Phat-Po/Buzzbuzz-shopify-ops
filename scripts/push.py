#!/usr/bin/env python3
"""BuzzBuzz: 推送產品到 Shopify

用法:
  python scripts/push.py products/<product-dir>

讀取 product.yaml → 上傳圖片 → 透過 Shopify Admin GraphQL API 建立/更新產品
（含圖片/alt text/變體/價格）→ 所有產品預設為 DRAFT → 寫回 published 記錄到 product.yaml

技術說明：使用 productSet mutation（Shopify 官方目前建議的單一 mutation，
一次處理 title/description/選項/變體/圖片，取代已棄用的 productCreate +
productCreateMedia + productVariantsBulkCreate 三段式流程）。圖片上傳仍需先走
stagedUploadsCreate 兩段式流程（先拿上傳網址，把本地檔案傳上去，再把
resourceUrl 交給 productSet）。
"""

from __future__ import annotations

import sys
import json
import mimetypes
import itertools
from pathlib import Path
from datetime import datetime, timezone

import yaml
import httpx
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    shopify_store: str = ""
    shopify_admin_token: str = ""
    shopify_api_version: str = "2026-04"
    # 所有產品上架都要放進「Popo選物」這個 collection。用 ID 而不是名稱，
    # 這樣就算未來在 Shopify 後台把 collection 改名，這裡也不用跟著改。
    shopify_default_collection_id: str = "gid://shopify/Collection/318686199917"

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


def graphql_url(settings: Settings) -> str:
    return f"https://{settings.shopify_store}/admin/api/{settings.shopify_api_version}/graphql.json"


def graphql_headers(settings: Settings) -> dict:
    return {
        "X-Shopify-Access-Token": settings.shopify_admin_token,
        "Content-Type": "application/json",
    }


def build_base_fields(data: dict, settings: Settings) -> dict:
    """從 product.yaml 建立 productSet 的基本欄位（title/description/tags/seo/category/collection...）"""
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
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    input_data = {
        "title": title,
        "descriptionHtml": description_html,
        "productType": product_type,
        "vendor": vendor,
        "tags": tags,
        "status": "DRAFT",
    }

    seo = {}
    if data.get("seo_title"):
        seo["title"] = data["seo_title"]
    if data.get("seo_meta"):
        seo["description"] = data["seo_meta"]
    if seo:
        input_data["seo"] = seo

    # Shopify 官方標準分類（用 taxonomy ID，不是 shopify_category 那個純文字欄位）
    if data.get("shopify_taxonomy_id"):
        input_data["category"] = data["shopify_taxonomy_id"]

    # 所有產品都要放進預設 collection（Popo選物）
    if settings.shopify_default_collection_id:
        input_data["collections"] = [settings.shopify_default_collection_id]

    # URL handle：一定要是 ASCII slug，不然瀏覽器網址列會變成一長串 %E6%97%A5... 編碼
    if data.get("url_handle"):
        input_data["handle"] = data["url_handle"]

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
    # 注意：price_gap_note 不寫進 metafields（操作者要求移除）
    text_fields = {
        "brand_jp", "brand_en", "material", "dimensions",
        "country_of_origin", "season", "gender",
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


def build_category_attribute_metafields(client: httpx.Client, settings: Settings, product_gid: str, data: dict) -> list[dict]:
    """把 product.yaml 的 category_attributes（例: {Color: Blue, Target gender: Female}）
    轉成 Shopify 的分類屬性 metafields（product_taxonomy_value_reference 型別）。

    這是 Shopify Admin 商品頁「Category」卡片裡那些 Color/Target gender/Upper material
    之類的下拉選單欄位，跟一般 metafieldsSet 用的自訂欄位是不同機制：值不是文字，而是
    指向 Shopify 官方 TaxonomyValue 的 GID，且對應的 metafield definition 要用
    `product_taxonomy_attribute_handle` validation 綁定到 taxonomy attribute（用
    kebab-case handle，例如 "target-gender"），才會在 Category 卡片顯示。
    """
    category_attrs = data.get("category_attributes") or {}
    taxonomy_id = data.get("shopify_taxonomy_id")
    if not category_attrs or not taxonomy_id:
        return []

    query = """
    query($id: ID!) {
      node(id: $id) {
        ... on TaxonomyCategory {
          attributes(first: 50) {
            edges {
              node {
                __typename
                ... on TaxonomyChoiceListAttribute {
                  name
                  values(first: 250) {
                    edges { node { id name } }
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    resp = client.post(graphql_url(settings), json={"query": query, "variables": {"id": taxonomy_id}}, headers=graphql_headers(settings))
    resp.raise_for_status()
    body = resp.json()
    if "errors" in body:
        print(f"  ⚠️  查詢分類屬性失敗: {json.dumps(body['errors'], ensure_ascii=False)}")
        return []

    attr_edges = (body.get("data", {}).get("node") or {}).get("attributes", {}).get("edges", [])
    attrs_by_name = {}
    for edge in attr_edges:
        node = edge["node"]
        if node.get("__typename") != "TaxonomyChoiceListAttribute":
            continue
        values_by_name = {v["node"]["name"].lower(): v["node"]["id"] for v in node["values"]["edges"]}
        attrs_by_name[node["name"].lower()] = values_by_name

    metafields = []
    for attr_name, value_name in category_attrs.items():
        values_by_name = attrs_by_name.get(attr_name.lower())
        if values_by_name is None:
            print(f"  ⚠️  分類屬性「{attr_name}」不屬於這個 taxonomy category，跳過")
            continue
        value_id = values_by_name.get(str(value_name).lower())
        if value_id is None:
            print(f"  ⚠️  分類屬性「{attr_name}」沒有選項「{value_name}」，跳過")
            continue
        key = attr_name.lower().replace(" ", "_")
        metafields.append({
            "ownerId": product_gid,
            "namespace": "buzzbuzz",
            "key": key,
            "type": "product_taxonomy_value_reference",
            "value": value_id,
        })

    return metafields


def create_staged_upload(client: httpx.Client, settings: Settings, filename: str, mime_type: str) -> dict:
    """呼叫 stagedUploadsCreate，拿到暫存上傳目標（url + resourceUrl + parameters）"""
    mutation = """
    mutation stagedUploadsCreate($input: [StagedUploadInput!]!) {
      stagedUploadsCreate(input: $input) {
        stagedTargets {
          url
          resourceUrl
          parameters {
            name
            value
          }
        }
        userErrors {
          field
          message
        }
      }
    }
    """
    variables = {
        "input": [{
            "resource": "IMAGE",
            "filename": filename,
            "mimeType": mime_type,
            "httpMethod": "POST",
        }]
    }

    resp = client.post(graphql_url(settings), json={"query": mutation, "variables": variables}, headers=graphql_headers(settings))
    resp.raise_for_status()
    body = resp.json()

    if "errors" in body:
        sys.exit(f"❌ stagedUploadsCreate GraphQL 錯誤: {json.dumps(body['errors'], indent=2, ensure_ascii=False)}")

    result = body["data"]["stagedUploadsCreate"]
    if result["userErrors"]:
        for err in result["userErrors"]:
            print(f"  ⚠️  {err['field']}: {err['message']}")
        sys.exit("❌ 圖片暫存上傳目標建立失敗")

    return result["stagedTargets"][0]


def upload_file_to_staged_target(client: httpx.Client, target: dict, file_path: Path, mime_type: str) -> None:
    """把本地圖片檔案 POST 到 stagedUploadsCreate 給的暫存網址"""
    fields = {p["name"]: p["value"] for p in target["parameters"]}
    file_bytes = file_path.read_bytes()

    resp = client.post(
        target["url"],
        data=fields,
        files={"file": (file_path.name, file_bytes, mime_type)},
    )
    if resp.status_code >= 300:
        sys.exit(f"❌ 圖片上傳失敗 ({file_path.name}): HTTP {resp.status_code}\n{resp.text[:500]}")


def stage_and_upload_images(client: httpx.Client, settings: Settings, product_dir: Path, data: dict) -> list[dict]:
    """把 product.yaml 裡 images 清單的所有圖片上傳到 Shopify，回傳 productSet 用的 files input"""
    images = data.get("images", [])
    alt_texts = data.get("alt_texts", {}) or {}

    files_input = []
    for rel_path in images:
        img_path = product_dir / rel_path
        if not img_path.exists():
            print(f"  ⚠️  找不到圖片，跳過: {img_path}")
            continue

        mime_type = mimetypes.guess_type(img_path.name)[0] or "application/octet-stream"
        target = create_staged_upload(client, settings, img_path.name, mime_type)
        upload_file_to_staged_target(client, target, img_path, mime_type)

        files_input.append({
            "originalSource": target["resourceUrl"],
            "alt": alt_texts.get(rel_path, ""),
            "filename": img_path.name,
            "contentType": "IMAGE",
        })
        print(f"  🖼️  已上傳: {rel_path}")

    return files_input


def build_options_and_variants(data: dict) -> tuple[list[dict], list[dict]]:
    """把 product.yaml 的 variants（顏色/尺寸選項）轉成 productSet 的 productOptions + variants"""
    variants_spec = data.get("variants", []) or []
    valid_options = [v for v in variants_spec if v.get("option") and v.get("values")]

    price = data.get("price_twd") or 0
    compare_at = data.get("price_tw_ref") or 0
    compare_at_price = str(compare_at) if compare_at and compare_at > price else None

    if not valid_options:
        # 沒填變體：建立單一預設變體，仍要帶上價格
        options_input = [{"name": "Title", "position": 1, "values": [{"name": "Default Title"}]}]
        variant = {
            "price": str(price),
            "optionValues": [{"optionName": "Title", "name": "Default Title"}],
        }
        if compare_at_price:
            variant["compareAtPrice"] = compare_at_price
        return options_input, [variant]

    options_input = [
        {
            "name": opt["option"],
            "position": i,
            "values": [{"name": v} for v in opt["values"]],
        }
        for i, opt in enumerate(valid_options, start=1)
    ]

    option_names = [opt["option"] for opt in valid_options]
    value_lists = [opt["values"] for opt in valid_options]

    variants_input = []
    for combo in itertools.product(*value_lists):
        variant = {
            "price": str(price),
            "optionValues": [
                {"optionName": option_names[i], "name": combo[i]}
                for i in range(len(combo))
            ],
        }
        if compare_at_price:
            variant["compareAtPrice"] = compare_at_price
        variants_input.append(variant)

    return options_input, variants_input


def product_set(client: httpx.Client, settings: Settings, input_data: dict, existing_id: str | None) -> dict:
    """呼叫 productSet 建立/更新產品（含選項、變體、圖片）"""
    mutation = """
    mutation productSet($input: ProductSetInput!, $synchronous: Boolean!, $identifier: ProductSetIdentifiers) {
      productSet(input: $input, synchronous: $synchronous, identifier: $identifier) {
        product {
          id
          handle
          onlineStorePreviewUrl
          status
          variants(first: 50) {
            nodes {
              id
              price
            }
          }
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
        "synchronous": True,
        "identifier": {"id": existing_id} if existing_id else None,
    }

    resp = client.post(graphql_url(settings), json={"query": mutation, "variables": variables}, headers=graphql_headers(settings))
    resp.raise_for_status()
    body = resp.json()

    if "errors" in body:
        sys.exit(f"❌ productSet GraphQL 錯誤: {json.dumps(body['errors'], indent=2, ensure_ascii=False)}")

    result = body["data"]["productSet"]
    if result["userErrors"]:
        for err in result["userErrors"]:
            print(f"  ⚠️  {err['field']}: {err['message']}")
        sys.exit("❌ 產品建立/更新失敗")

    return result["product"]


def set_metafields(client: httpx.Client, settings: Settings, product_gid: str, metafields: list[dict]) -> None:
    """批次寫入 metafields"""
    if not metafields:
        return

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

    resp = client.post(graphql_url(settings), json={"query": mutation, "variables": {"metafields": metafields}}, headers=graphql_headers(settings))
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
    """主流程：讀取 → 上傳圖片 → 推送產品(含選項/變體) → 寫入 metafields → 寫回記錄"""
    settings = Settings()

    if not settings.shopify_store or not settings.shopify_admin_token:
        sys.exit("❌ 請先設定 .env 檔案（SHOPIFY_STORE 和 SHOPIFY_ADMIN_TOKEN）")

    data = load_product(product_dir)
    product_name = data.get("product_name") or product_dir.name

    published = data.get("published", {}) or {}
    existing_id = published.get("shopify_id") or None

    print(f"\n🚀 推送: {product_name}")
    if existing_id:
        print(f"  ℹ️  已發布過 (Shopify ID: {existing_id})，將更新既有產品（圖片/選項/變體/價格）")

    with httpx.Client(timeout=60) as client:
        # 1. 上傳圖片
        files_input = stage_and_upload_images(client, settings, product_dir, data)

        # 2. 建立選項 + 變體
        options_input, variants_input = build_options_and_variants(data)

        # 3. 組合 productSet input，一次送出 title/description/選項/變體/圖片
        input_data = build_base_fields(data, settings)
        if files_input:
            input_data["files"] = files_input
        input_data["productOptions"] = options_input
        input_data["variants"] = variants_input

        shopify_product = product_set(client, settings, input_data, existing_id)
        product_gid = shopify_product["id"]
        product_url = shopify_product.get("onlineStorePreviewUrl") or shopify_product.get("onlineStoreUrl") or ""
        variant_count = len(shopify_product.get("variants", {}).get("nodes", []))

        print(f"  ✅ 產品已{'更新' if existing_id else '建立'}")
        print(f"  📦 Shopify ID: {product_gid}")
        print(f"  🖼️  圖片: {len(files_input)} 張")
        print(f"  🏷️  變體: {variant_count} 個")
        print(f"  🔗 預覽連結: {product_url}")

        # 4. 寫入 metafields（一般欄位 + 分類屬性）
        metafields = build_metafields_input(product_gid, data)
        metafields += build_category_attribute_metafields(client, settings, product_gid, data)
        if metafields:
            set_metafields(client, settings, product_gid, metafields)

    # 寫回發布記錄
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
