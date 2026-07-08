# Handoff: Mont-bell 第一個產品頁完成，流程跑通

> 日期：2026-07-08
> 上一個 handoff：無（本專案第一次 handoff）

## 本會話完成了什麼

1. **從 6 個可推進品牌中選定 Mont-bell 開始**，完成 `Superior Down Round Neck 800FP 男款` 完整產品頁
2. **跑通 9 步工作流**：選品調研 → 定價調研 → 建立資料夾 → 抓取產品圖 → 填基本欄位 → AI 文案 → 質檢 → 推送 Shopify
3. **建立並更新了 AGENTS.md 流程規則**：定價策略（台灣行情優先、20% 毛利自動過關線）、圖片抓取步驟、成本保密、價格來源存檔

## 當前狀態

- Mont-bell Superior Down Round Neck 已在 Shopify **DRAFT**（未發布）
- Shopify ID: `gid://shopify/Product/8149719515245`
- 預覽：https://v0orwve1oqbhzf2s-69710020717.shopifypreview.com/products_preview?preview_key=96a791af24c7b5c52943b0dfb2159ff0
- 質檢：17/17（100%）
- 售價：TWD 3,980（成本 TWD 2,884，毛利 27%）

## 下一步任務

從 `tasks/next-agent-actionable-brands.md` 選下一個 SKU：

**優先順序**：
1. Mont-bell Storm Cruiser 或 Plasma 1000（品牌調研已存檔，直接跳步驟①）
2. KATO 鐵道模型（#61）— 無代理風險
3. Gashapon 轉蛋整套（#69）— 成本最低、驗證最快
4. Human Made — 第二波（調研已存檔在 `sourcing/radar/human-made-brief.md`）

## 已知問題：Variant 顏色圖片未完整抓取

**當前情況**：只抓了 Black（photo-01）的主圖和 Olive Green（photo-02~06）的模特/細節圖。

**Mont-bell 產品頁 JSON 中有 5 色主圖**：
- `1101666_bk.webp` — Black（已抓 ✅）
- `1101666_bl.webp` — Blue/Navy（未抓 ❌）
- `1101666_dgn.webp` — Dark Green（未抓 ❌）
- `1101666_og.webp` — Olive Green（未抓 ❌）
- `1101666_tn25.webp` — Tan/Beige（未抓 ❌）

**需要的修復**：每個顏色 variant 至少抓一張主圖（`/storage/products/images/origin/1101666_<color>.webp`），讓 Shopify 的顏色選項對應到正確的產品圖片。

**正確的抓圖做法**（已寫入 AGENTS.md 步驟③）：
1. `curl` 下載頁面 HTML
2. `grep` 搜尋頁面中 `"images":` JSON 物件，取得所有顏色的 `image_url_origin`
3. 下載每個顏色的主圖 + 選一個顏色的 cut_images（模特/細節圖）
4. 不要直接抓 img tag（會拿到 UI 元件）

## 流程變更記錄（已寫入 AGENTS.md）

本會話對 AGENTS.md 的關鍵修改：
- 新增「定價策略」章節：台灣行情優先 > 干森費率、20% 毛利自動過關線
- 工作流從 8 步擴展到 9 步，新增步驟③（抓取產品圖片）
- 步驟①明確定義為執行步驟非決策關卡
- 成本結構永不公開（shipping-costs.yaml 已加註機密標記）

## 調研存檔（以後不重查）

| 檔案 | 用途 |
|------|------|
| `sourcing/radar/mont-bell-brief.md` | Mont-bell 品牌級調研（熱門 SKU、通路、價差） |
| `sourcing/radar/human-made-brief.md` | Human Made 品牌調研（備用） |
| `sourcing/price-refs/mont-bell-superior-down-roundneck.md` | 台灣價格來源 + 日本官網連結（需操作者認證） |

## 操作者待辦

- [ ] 在 Shopify Admin 預覽確認產品內容無誤後手動 publish
- [ ] 認證 `sourcing/price-refs/mont-bell-superior-down-roundneck.md` 中的台灣價格來源
- [ ] 日本官網下單：https://www.montbell.com/jp/en/products/detail/1101666

## 驗證指令（下次開始前跑）

```bash
git status --short
python scripts/check.py products/mont-bell-superior-down-roundneck
python scripts/status.py
```
