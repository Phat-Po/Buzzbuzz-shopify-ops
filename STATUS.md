# BuzzBuzz 日本選物店 — Status

## ▲ Current

---

## 2026-07-08 | push.py 補完圖片/變體/分類/collection，供應鏈保密規則收斂

**Done this session:**
- `push.py` 改用 `productSet` mutation（Shopify 目前建議的單一 mutation，取代已棄用的
  `productCreate` + `productCreateMedia` + `productVariantsBulkCreate` 三段式流程）：
  一次送出 title/description/選項(variants)/價格/圖片，圖片走 `stagedUploadsCreate`
  兩段式上傳（先拿暫存網址，把本地檔案傳上去，再交給 productSet）
- 新增支援對已發布產品重跑 `push.py`＝更新（`productSet` 的 `identifier` 比對既有
  Shopify ID），不再是舊版「已發布過就跳過」
- 補上 `shopify_taxonomy_id`（Shopify 官方標準分類）與 `shopify_default_collection_id`
  （所有產品自動歸進「Popo選物」collection，用 ID 不是名稱，改名不影響）
- 修了一個真實的供應鏈保密違規：`description_fact` 曾寫出日本原廠定價（¥19,800），
  已改掉並補進 `check.py` 的自動掃描規則（擋 ¥xxx/日幣xxx/JPY xxx）
- Tags 從「brand:/category:/style:/origin:/gender: 六個標籤」簡化成固定一個
  `curated:popo-select`——查證 Shopify 官方文件後確認細分標籤沒有被列為 Agentic
  Storefronts 會同步給 AI 助手的欄位，簡化掉沒有實際效益的複雜度
- 在 Shopify 建了 5 個 metafield definition 並 pin（brand_en/material/price_gap_note/
  season/gender），後台商品頁現在看得到這些值（之前有寫入但沒 definition，UI 顯示
  「No metafields pinned」）
- CONVERSE TOKYO 這個產品已經用新版 push.py 重推過，Shopify 上現在有 8 張圖、正確
  選項/變體/價格、官方分類、collection

**Current state:**
`push.py`/`check.py`/`_template/product.yaml` 的改動都完成且驗證過（對 CONVERSE TOKYO
實際 push 到 Shopify 確認）。CONVERSE TOKYO 產品目前 tags 還是舊格式（6 個），本輪只
改了 template 和 push.py 邏輯，還沒重新 push 讓新 tag scheme 生效（操作者要求先不要
再 push，之後自己決定時機）。

**Next steps:**
1. 找操作者確認時機後，重推 CONVERSE TOKYO 讓新 tag（`curated:popo-select`）生效
2. 繼續往下跑選品（`sourcing/radar/` 或 `top100-validation-sweep-plan.md`）

**Decisions / notes:**
- Tags 對傳統 Google SEO 沒有直接幫助；對 AI agent 的幫助也沒有 Shopify 官方保證
  （官方列出的同步欄位是 title/description/options/images/price/availability，不含
  tags）——固定一個 curation tag 就夠，不用堆疊細分標籤
- `cost_jpy` 允許寫進 Shopify metafields（操作者定價需要），但只放 admin-only
  metafield，絕對不能出現在任何公開文案欄位

## ■ Milestones

- 2026-07-08 選品雷達上線（`sourcing/radar/` discovery+validation 兩層方法論）+ 打通 Shopify OAuth（`scripts/oauth_setup.py`）+ 第一個產品（CONVERSE TOKYO）成功推送 Shopify DRAFT | ✅ done
- 2026-07-07 項目重新定位：從 ERP 改為本地 CLI 上稿工具，建立 products/YAML 模板、三個 CLI 腳本、Top100 選品清單 | ✅ done

## ▼ Archive

- 2026-07-07 MVP-0: FastAPI + SQLite web dashboard (已廢棄，保留在 git history)
