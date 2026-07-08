# BuzzBuzz 日本選物店 — Status

## ▲ Current

---

## 2026-07-08 | 選品雷達上線 + 第一個產品成功推送 Shopify（DRAFT）

**Done this session:**
- 建立「台灣選品雷達輕量版」（`sourcing/radar/`）：discovery（場景詞搜尋，不預設品牌）+ validation（Google Trends TW / 社群討論量 / 第三方交叉比對 / 蝦皮市場證據，2-of-4 收斂）兩層架構，取代單純依賴 `top100.yaml`
- 跑完第一輪 discovery 全循環（dcard/ptt/mobile01 × 17場景詞），驗證 8 個候選品牌，結果見 `sourcing/radar/candidates.md`：**Converse Tokyo 日本限定**是唯一無條件強候選（台灣無官方通路）；BEAMS/LOGOS/Twinbird/Chiikawa 都命中訊號但台灣已有官方代理/直營，只能做「代理沒引進的限定款」
- 寫了 `tasks/top100-validation-sweep-plan.md`（top100.yaml 剩餘 97 品牌的驗證專用掃描計劃，跟 discovery 分開）
- 第一次打通完整上稿流程：建立 `products/converse-tokyo-allstar-10th-navy/`（型號 A2854PSH900，官網真實查證資料）→ AI 生成繁中文案 → `check.py` 質檢 17/17 → `push.py` 成功推送 Shopify（DRAFT，Product ID `8148497727597`）
- 打通 Shopify Admin API 授權：2026年起 custom app 不再直接顯示 `shpat_` token，改用 Client ID/Secret；付費正式商店不能用 client_credentials grant，改走 authorization code grant（用 `cloudflared` 臨時通道處理跨地點授權），寫成可重用工具 `scripts/oauth_setup.py`
- 修了 `push.py` 兩個真實 bug：缺 `pydantic-settings` 依賴、GraphQL mutation 宣告未使用的 `$metafields` 變數
- 加了「供應鏈保密」自動掃描（`check.py` 第17項檢查）：擋下「向官網下單」「官網缺貨」「台灣沒有代理」這類會洩露商業模式的文案用語，規則同步寫進 `AGENTS.md` 和 `products/_template/product.yaml`

**Current state:**
`.env` 已有永久有效的 Shopify 憑證，可直接用。第一個產品是 Shopify 上的真實 DRAFT，但**只有標題/描述/tags/metafields，沒有圖片、沒有變體/價格**——`push.py` 目前完全沒處理 `images`/`variants`/`alt_text` 這三個欄位，是下一步要補的缺口。`sourcing/radar/` 的驗證方法論已經穩定，可以繼續往下跑（top100 剩餘品牌 或 discovery 下一輪）。

**Next steps:**
1. 補 `push.py` 的圖片上傳（`stagedUploadsCreate` + media mutation）與變體/價格（`productVariantsBulkCreate` 之類），完整交接文件見 `tasks/handoff-image-variant-upload.md`
2. 之後可選：跑 `tasks/top100-validation-sweep-plan.md` 的品牌驗證掃描，或對已有候選（LOGOS/Twinbird/Chiikawa）補 D-2 毛價差試算

**Decisions / notes:**
- 選品驗證不再只信 `top100.yaml`——2-of-4 訊號收斂 + 「有代理不代表沒機會，要查毛價差」是現在的方法論
- 產品文案有明確的供應鏈保密紅線，`check.py` 已自動守門
- Shopify custom app 授權流程 2026 年整個改版，細節記在 `scripts/oauth_setup.py` 註解裡，之後不用重查

## ■ Milestones

- 2026-07-07 項目重新定位：從 ERP 改為本地 CLI 上稿工具，建立 products/YAML 模板、三個 CLI 腳本、Top100 選品清單 | ✅ done

## ▼ Archive

- 2026-07-07 MVP-0: FastAPI + SQLite web dashboard (已廢棄，保留在 git history)
