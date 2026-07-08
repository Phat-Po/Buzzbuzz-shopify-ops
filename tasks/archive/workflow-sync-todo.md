# Task：AGENTS.md / STATUS.md 需要跟 push.py 的實際改動同步

`scripts/push.py`、`scripts/check.py`、`products/_template/product.yaml` 已經改了(目前
還沒 commit),但 `AGENTS.md`(工作流說明)、`STATUS.md`(進度記錄)還是舊的，兩邊對不上。
這份文件只列出「建議怎麼改」，**不直接動 AGENTS.md/STATUS.md，要操作者看過同意才改**。

## push.py 實際的新行為（跟 AGENTS.md 現在寫的對不上的地方）

- 現在會上傳 `images/` 圖片（`stagedUploadsCreate` 兩段式）+ 帶 alt text，AGENTS.md 工作流 ⑥ 只寫「推送到 Shopify」，沒提圖片
- 現在會把 `variants` 轉成 Shopify 選項+變體+價格，AGENTS.md 完全沒提
- 改用 `productSet` mutation，新增：已發布產品可以重跑 `push.py` 直接更新（舊版只能建立一次）
- 新增 `shopify_default_collection_id`（寫死在 push.py 裡，所有產品自動歸類到「Popo選物」這個 collection）— AGENTS.md 沒提到有這個設定，也沒說在哪裡改
- `product.yaml` 新增 `shopify_taxonomy_id` 欄位（Shopify 官方標準分類），AGENTS.md 工作流 ② 沒提到要填這個
- `check.py` 供應鏈保密掃描新增規則：擋日本原廠定價（¥xxx / 日幣xxx / JPY xxx），AGENTS.md 的 Constraints 供應鏈保密段落只提到「不寫進貨來源/官網庫存」，沒提「不寫原廠定價」

## 建議怎麼改（等你確認）

1. **AGENTS.md 工作流 ⑥**：補充說明推送時會一併處理圖片/變體/價格/collection，且支援對已發布產品重跑＝更新
2. **AGENTS.md 工作流 ②**：補充需要查 `shopify_taxonomy_id`（用 Admin GraphQL `taxonomy { categories(search:...) }` 查）
3. **AGENTS.md Constraints 供應鏈保密段落**：補上「也不寫日本原廠定價」
4. **AGENTS.md Directory Layout**：補上 `sourcing/radar/`、`scripts/oauth_setup.py`；新增一小段說明 `shopify_default_collection_id` 是寫死在 push.py 裡，不是 `.env`
5. **STATUS.md**：目前「Next steps」還寫著「補圖片上傳」，但這件事已經做了，內容需要更新反映實況
6. **`tasks/handoff-image-variant-upload.md`**：裡面描述的任務已經完成，可以標記解決或封存

## 還沒處理、但跟這個任務有關的事

- 這批改動（push.py/check.py/template）本身還沒 commit
- CONVERSE TOKYO 那個產品是用舊版 push.py 建立的，還沒用新版重推過，Shopify 上目前應該還是沒圖沒變體的狀態

以上要不要改、改多少，等操作者一項一項確認。
