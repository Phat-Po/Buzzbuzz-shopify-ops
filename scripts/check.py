#!/usr/bin/env python3
"""BuzzBuzz: Agent-Ready 產品質檢

用法:
  python scripts/check.py products/<product-dir>    檢查單一產品
  python scripts/check.py --all                       檢查所有產品

檢查清單（Shopify Spring '26 Agentic Commerce 標準）:
  ✅ 標題 ≤150 字
  ✅ 三段描述 (Fact/Feel/Trust) 均非空
  ✅ SEO title ≤60 字
  ✅ SEO meta ≤160 字
  ✅ 規格 (material/dimensions/weight) 至少一項
  ✅ 每張圖片都有 alt text
  ✅ FAQ ≥3 組
  ✅ Tags 含固定的 curated:popo-select 標籤
  ✅ JSON-LD schema 有效
  ✅ 圖片清單非空
  ✅ 售價 > 0
  ✅ 供應鏈保密（文案不得洩露進貨來源/官網庫存/競業分析用語）
"""

from __future__ import annotations

import re
import sys
import json
from pathlib import Path

import yaml


# 供應鏈保密：客戶看得到（或 AI agent 讀得到）的文案裡，不能出現進貨來源、
# 官網庫存監控、競業分析式的用語（例如「向官網下單」「台灣沒有代理」），
# 也不能揭露日本原廠定價（¥xxx / 日幣xxx），這會讓人反推我們的進貨成本與利潤空間。
# 這些是內部資訊，寫進公開文案等於告訴別人我們的商業模式。
SOURCING_LEAK_PATTERNS = [
    r"官網下單", r"官方網站下單", r"向.{0,15}官網.{0,6}下單", r"向.{0,20}官方網站.{0,6}下單",
    r"官網.{0,4}(缺貨|現貨|有庫存|無庫存|在庫)",
    r"(沒有|無).{0,10}(官方|代理).{0,10}(通路|管道)", r"(沒有|無).{0,6}代理商",
    r"直接向.{0,20}下單", r"跟.{0,10}官網.{0,6}買", r"官網.{0,6}進貨",
    r"¥[\d,]+", r"日幣.{0,4}[\d,]+", r"日圓.{0,4}[\d,]+", r"JPY.{0,4}[\d,]+",
    r"日本(定價|售價|原價|訂價).{0,10}[\d,]+",
]

# 每個產品固定只掛這一個標籤（標記「Popo 精選」），不再自己編 brand:/category:/style: 這些
CURATION_TAG = "curated:popo-select"

# 掃描這些欄位——凡是最終會出現在 Shopify 商品頁、metafields，或設計上將來要推送
# 給 AI agent 讀取的內容，都算「公開文案」，用同一標準檢查。
PUBLIC_FACING_TEXT_FIELDS = [
    "title_zh", "seo_title", "seo_meta",
    "description_fact", "description_feel", "description_trust",
    "price_gap_note", "jsonld_product", "jsonld_faq",
]


def _collect_public_text(data: dict) -> list[tuple[str, str]]:
    """回傳 [(欄位名, 文字內容), ...]，含 FAQ 的每組 q/a"""
    texts = []
    for field in PUBLIC_FACING_TEXT_FIELDS:
        v = data.get(field)
        if v:
            texts.append((field, str(v)))
    for i, item in enumerate(data.get("faq") or []):
        if item.get("q"):
            texts.append((f"faq[{i}].q", item["q"]))
        if item.get("a"):
            texts.append((f"faq[{i}].a", item["a"]))
    return texts


def _check_sourcing_confidentiality(data: dict) -> bool:
    return len(_sourcing_leak_hits(data)) == 0


def _sourcing_leak_hits(data: dict) -> list[str]:
    hits = []
    for field, text in _collect_public_text(data):
        for pattern in SOURCING_LEAK_PATTERNS:
            if re.search(pattern, text):
                hits.append(f"{field}: 命中「{pattern}」")
    return hits


def _sourcing_confidentiality_detail(data: dict) -> str:
    hits = _sourcing_leak_hits(data)
    if not hits:
        return "沒有偵測到供應鏈洩露用語"
    return " ｜ ".join(hits[:3]) + (f"（共 {len(hits)} 處）" if len(hits) > 3 else "")


CHECKLIST = [
    {
        "id": "title_zh",
        "label": "繁中標題",
        "fn": lambda d: bool(d.get("title_zh")),
        "detail": lambda d: f"目前: '{d.get('title_zh', '')[:50]}...'" if d.get('title_zh') else "尚未填寫",
        "hint": "格式: [日本品牌] [商品類型] [關鍵屬性] [差異點] | BuzzBuzz 日本選物",
    },
    {
        "id": "title_length",
        "label": "標題長度 ≤150 字",
        "fn": lambda d: len(d.get("title_zh") or "") <= 150,
        "detail": lambda d: f"目前: {len(d.get('title_zh') or '')} 字",
        "hint": "標題太長不利 SEO，控制在 150 字內",
    },
    {
        "id": "description_fact",
        "label": "Fact 段描述",
        "fn": lambda d: bool(d.get("description_fact")),
        "detail": lambda d: f"目前: {len(d.get('description_fact') or '')} 字",
        "hint": "材質、尺寸、重量、日本售價、台灣參考價",
    },
    {
        "id": "description_feel",
        "label": "Feel 段描述",
        "fn": lambda d: bool(d.get("description_feel")),
        "detail": lambda d: f"目前: {len(d.get('description_feel') or '')} 字",
        "hint": "穿搭建議、使用場景、適合風格",
    },
    {
        "id": "description_trust",
        "label": "Trust 段描述",
        "fn": lambda d: bool(d.get("description_trust")),
        "detail": lambda d: f"目前: {len(d.get('description_trust') or '')} 字",
        "hint": "正品保證、日本直送、退換貨政策",
    },
    {
        "id": "seo_title",
        "label": "SEO 標題",
        "fn": lambda d: bool(d.get("seo_title")),
        "detail": lambda d: f"目前: '{d.get('seo_title', '')[:50]}'" if d.get('seo_title') else "尚未填寫",
        "hint": "≤60 字，含品牌+商品名+關鍵詞",
    },
    {
        "id": "seo_title_length",
        "label": "SEO 標題長度 ≤60 字",
        "fn": lambda d: len(d.get("seo_title") or "") <= 60,
        "detail": lambda d: f"目前: {len(d.get('seo_title') or '')} 字",
        "hint": "超過 60 字會被 Google 截斷",
    },
    {
        "id": "seo_meta",
        "label": "SEO Meta Description",
        "fn": lambda d: bool(d.get("seo_meta")),
        "detail": lambda d: f"目前: '{d.get('seo_meta', '')[:50]}'" if d.get('seo_meta') else "尚未填寫",
        "hint": "≤160 字，含價差/日本直送/限定的銷售點",
    },
    {
        "id": "seo_meta_length",
        "label": "SEO Meta 長度 ≤160 字",
        "fn": lambda d: len(d.get("seo_meta") or "") <= 160,
        "detail": lambda d: f"目前: {len(d.get('seo_meta') or '')} 字",
        "hint": "超過 160 字會被 Google 截斷",
    },
    {
        "id": "specs",
        "label": "規格資訊（至少一項）",
        "fn": lambda d: bool(d.get("material") or d.get("dimensions") or d.get("weight_g")),
        "detail": lambda d: f"材質:{bool(d.get('material'))} 尺寸:{bool(d.get('dimensions'))} 重量:{bool(d.get('weight_g'))}",
        "hint": "AI agent 需要結構化規格才能比價和推薦",
    },
    {
        "id": "alt_texts",
        "label": "圖片 Alt Text",
        "fn": lambda d: _check_alt_texts(d),
        "detail": lambda d: _alt_text_detail(d),
        "hint": "每張圖片都要有繁中 alt text，AI 搜尋透過 alt text 理解圖片內容",
    },
    {
        "id": "faq",
        "label": "FAQ ≥3 組",
        "fn": lambda d: len(d.get("faq") or []) >= 3,
        "detail": lambda d: f"目前: {len(d.get('faq') or [])} 組",
        "hint": "AI 搜尋（Google AI Overviews、ChatGPT）特別喜歡引用 FAQ",
    },
    {
        "id": "tags",
        "label": "Shopify 標籤",
        "fn": lambda d: _check_tags(d),
        "detail": lambda d: f"目前: {d.get('tags') or []}",
        "hint": f"每個產品固定只掛一個標籤 {CURATION_TAG!r}，不用再自己編 brand:/category:/style: 這些",
    },
    {
        "id": "jsonld_product",
        "label": "JSON-LD Product Schema",
        "fn": lambda d: _check_jsonld(d.get("jsonld_product")),
        "detail": lambda d: "有效 JSON" if _check_jsonld(d.get("jsonld_product")) else "無效或空白",
        "hint": "Product + Offer + Brand schema，讓 AI agent 準確讀取價格和庫存",
    },
    {
        "id": "images",
        "label": "圖片清單",
        "fn": lambda d: bool(d.get("images")),
        "detail": lambda d: f"目前: {len(d.get('images') or [])} 張",
        "hint": "至少一張產品圖片才能被 Shopify Catalog 收錄",
    },
    {
        "id": "price_twd",
        "label": "售價 > NT$0",
        "fn": lambda d: (d.get("price_twd") or 0) > 0,
        "detail": lambda d: f"目前: NT${d.get('price_twd', 0)}",
        "hint": "售價為 0 的產品不會被 Catalog 收錄",
    },
    {
        "id": "sourcing_confidentiality",
        "label": "供應鏈保密（不得洩露進貨來源）",
        "fn": _check_sourcing_confidentiality,
        "detail": _sourcing_confidentiality_detail,
        "hint": "文案裡不能出現「向官網下單」「官網缺貨」「台灣沒有代理」這類洩露商業模式/競業分析的用語，也不能寫日本原廠定價（¥xxx/日幣xxx）。庫存問題用 variants/stock_status 反映，不要在文案裡解釋原因",
    },
]


def _check_alt_texts(data: dict) -> bool:
    images = data.get("images") or []
    alt_texts = data.get("alt_texts") or {}
    if not images:
        return False
    return all(img in alt_texts and alt_texts[img] for img in images)


def _alt_text_detail(data: dict) -> str:
    images = data.get("images") or []
    alt_texts = data.get("alt_texts") or {}
    if not images:
        return "尚無圖片"
    covered = sum(1 for img in images if img in alt_texts and alt_texts[img])
    return f"{covered}/{len(images)} 張有 alt text"


def _check_tags(data: dict) -> bool:
    tags = data.get("tags") or []
    return CURATION_TAG in tags


def _check_jsonld(text: str | None) -> bool:
    if not text:
        return False
    try:
        json.loads(text)
        return True
    except (json.JSONDecodeError, TypeError):
        return False


def resolve_product_name(data: dict, dir_name: str) -> str:
    return data.get("product_name") or data.get("brand_jp") or dir_name


def check_product(product_dir: Path) -> dict:
    """檢查單一產品，回傳結果 dict"""
    yaml_path = product_dir / "product.yaml"
    if not yaml_path.exists():
        return {"name": product_dir.name, "error": "找不到 product.yaml", "results": [], "score": 0}

    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    name = resolve_product_name(data, product_dir.name)
    status = data.get("status", "draft")

    results = []
    for item in CHECKLIST:
        passed = item["fn"](data)
        results.append({
            "id": item["id"],
            "label": item["label"],
            "passed": passed,
            "detail": item["detail"](data),
        })

    score = sum(1 for r in results if r["passed"])
    total = len(results)

    return {
        "name": name,
        "status": status,
        "results": results,
        "score": score,
        "total": total,
    }


def print_result(result: dict) -> None:
    """印出單一產品檢查結果"""
    name = result["name"]
    status = result["status"]
    score = result["score"]
    total = result["total"]
    pct = int(score / total * 100)

    emoji = "🟢" if pct >= 80 else "🟡" if pct >= 50 else "🔴"

    print(f"\n{'─'*60}")
    print(f"  {emoji} {name}")
    print(f"  狀態: {status}  |  Agent-Ready: {score}/{total} ({pct}%)")
    print(f"{'─'*60}")

    for r in result["results"]:
        icon = "✅" if r["passed"] else "❌"
        print(f"  {icon} {r['label']}")
        print(f"     {r['detail']}")

    # Show hints for failed items
    failed = [r for r in result["results"] if not r["passed"]]
    if failed:
        print(f"\n  💡 改善建議:")
        for r in failed:
            full_item = next((c for c in CHECKLIST if c["id"] == r["id"]), None)
            if full_item:
                print(f"     [{r['label']}] {full_item['hint']}")

    print()


def main():
    if len(sys.argv) < 2:
        sys.exit("用法: python scripts/check.py <product-dir> | --all")

    if sys.argv[1] == "--all":
        base = Path("products")
        if not base.is_dir():
            sys.exit("❌ 找不到 products/ 目錄")

        dirs = [d for d in base.iterdir() if d.is_dir() and not d.name.startswith("_")]
        if not dirs:
            print("📭 尚無產品目錄")
            return

        total_score = 0
        total_items = 0
        for d in sorted(dirs):
            result = check_product(d)
            if "error" in result:
                print(f"  ⚠️  {d.name}: {result['error']}")
                continue
            print_result(result)
            total_score += result["score"]
            total_items += result["total"]

        if total_items > 0:
            overall = int(total_score / total_items * 100)
            print(f"{'='*60}")
            print(f"  總體 Agent-Ready: {total_score}/{total_items} ({overall}%)")
            print(f"{'='*60}\n")
    else:
        product_dir = Path(sys.argv[1])
        if not product_dir.is_dir():
            sys.exit(f"❌ 找不到目錄: {product_dir}")

        result = check_product(product_dir)
        if "error" in result:
            sys.exit(f"❌ {result['error']}")
        print_result(result)


if __name__ == "__main__":
    main()
