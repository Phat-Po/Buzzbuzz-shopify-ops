# Handoff: Chrome Extension V1 完成 → 下一階段

**日期**: 2026-07-08
**來源**: BuzzBuzz Chrome Extension 實作完成後
**對象**: 下一個 Claude session

---

## 一、本次完成

Chrome Extension（`chrome-extension/`）已完整建置，16 個檔案，~1,200 行 JS：

| 能力 | 狀態 |
|------|------|
| Converse Tokyo（converse-tokyo.jp）擷取 | ✅ 已驗證 |
| Shopify .json 通用擷取 | ✅ 待驗證 |
| Mont-bell DOM 擷取 | ✅ 待驗證 |
| YAML 骨架匯出 | ✅ |
| 圖片 ZIP 打包下載 | ✅ |
| 剪貼簿複製 YAML | ✅ |

---

## 二、遺留問題（需要下一個對話處理）

### 2.1 商品類型自動分類不準

converse-tokyo extractor 用 `window.location.pathname` 匹配 `category_id`，但 converse-tokyo.jp 的 category_id 不在 URL 裡（藏在頁面選單 HTML 中），所以 `product_type` 永遠空白。

**建議修法**：從頁面麵包屑（breadcrumb）或全域選單結構中提取分類資訊。或是乾脆讓 Claude 在補 AI 區段時一起填——因為 Claude 看商品名就能分（ALL STAR J OX → 潮流服飾 / 鞋類）。

### 2.2 url_handle 自動產生邏輯

converse-tokyo extractor 已從 URL 提取 SKU（`A2854PSH900`），組合成 `converse-tokyo-a2854psh900`。**這個是對的**。但操作者測試時說沒看到變化——需確認 popup 是否正確顯示了這個值。如果是空白的，可能是 SKU regex 沒匹配到某些 URL pattern。

### 2.3 售價 (price_twd) 永遠是 0

這是 design choice，不是 bug。售價是商業決策，Extension 不應該替操作者定價。**但**可以在下一個 Claude session 補 AI 區段時，用公式自動計算（例如 `cost_jpy * 0.3` 匯率換算後取整）。

---

## 三、架構問題：兩條工作流的整合（重要）

現在有兩條「把產品資料餵進 `products/`」的路徑：

```
路徑 A（Extension）:
  Chrome Extension 擷取 → 下載 ZIP → 操作者解壓到 products/<sku>/
  → product.yaml 骨架（基本欄位有、AI 欄位空白）

路徑 B（Claude 直接寫）:
  操作者給品牌/型號 → Claude 建立 products/<name>/
  → 從頭撰寫完整 product.yaml（含 AI 區段）
```

兩條路徑最終都走同一條發布管線：
```
products/<name>/product.yaml → python scripts/check.py → 審核 → python scripts/push.py
```

**需要解決的三個問題**：

### 3.1 格式對齊

Extension 輸出的 YAML 和 Claude 手寫的 YAML 必須欄位一致，這樣 `check.py` 和 `push.py` 才能通用。

目前 Extension 的 `yaml-builder.js` 已經對齊 `products/_template/product.yaml`（上次驗證 check.py 6/17 pass，11 個 AI 區段空白）。**格式已對齊。** 但需確認：
- `_body_html` 欄位（Extension 專有，給 Claude 參考用）不會干擾 `push.py`
- `images` 路徑格式一致（Extension 寫 `images/xxx.jpg` 相對路徑）

### 3.2 資料夾命名規則

這是格式對齊之外的另一個潛在衝突點。目前兩條路徑的命名邏輯不同：

| 路徑 | 命名邏輯 | 範例 |
|------|---------|------|
| Extension | url_handle（`converse-tokyo-a2854psh900`） | 自動，從 SKU 推導 |
| Claude 手寫 | 操作者指定（`converse-tokyo-allstar-10th-navy`） | 手動，語意化命名 |

如果操作者用 Extension 擷取後解壓，資料夾名會是 kebab-case slug（例如 `converse-tokyo-a2854psh900`）。但如果 Claude 手寫一個同名產品，資料夾名可能不同（例如 `converse-tokyo-allstar-10th-navy`）。

這樣會導致 **同一個 SKU 有兩個不同資料夾名**，`push.py` 是以 `url_handle` 做產品 identity（`productSet` + `identifier`），所以兩個資料夾如果 `url_handle` 相同會互相覆蓋，如果不同則會建立兩個重複產品。

**建議**：下一階段定一個命名規則。例如：
- 資料夾名 = `{brand_en}-{sku}`（從 url_handle 或 SKU 推導）
- 或用 `url_handle` 作為唯一 key 來做查重

### 3.3 查重機制

產品查重是一個兩層問題：

**Layer 1: Shopify 端**（push.py 層）
- `push.py` 用 `productSet` + `identifier`（Shopify product ID）做 upsert
- 如果 `url_handle` 相同 → 覆蓋（update），不會重複建立
- 如果 `url_handle` 不同 → 建立新產品（可能重複）

**Layer 2: 本地 products/ 端**（檔案系統層）
- 目前沒有查重機制
- 如果操作者用 Extension 擷取 `A2854PSH900`，又讓 Claude 手寫同一個型號，會得到兩個資料夾

**建議方案**：

```
Before creating new product folder:
  1. Extract SKU from source (Extension or manual input)
  2. Scan all existing product.yaml files for matching SKU
     grep -r "A2854PSH900" products/*/product.yaml
  3. If match found:
     - Show existing product to operator
     - Ask: "Update existing? Create new variant? Skip?"
  4. If no match:
     - Create new folder with standardized name
```

或者更簡單：**在 `products/` 根目錄維護一個 `_registry.yaml`**：

```yaml
# products/_registry.yaml — SKU → folder mapping
A2854PSH900: converse-tokyo-allstar-10th-navy
1101501: mont-bell-superior-down-roundneck-mens
```

Extension 和 Claude 在建立新產品前，都先查這個 registry 看 SKU 是否已存在。

---

## 四、建議下一階段工作順序

1. **修 Extension 的 product_type 自動分類**（從頁面麵包屑或讓 Claude 補）
2. **定義資料夾命名規則**（SKU-based vs 語意命名）
3. **建立查重機制**（registry file 或 scan-based）
4. **端到端測試**：Extension 擷取 → 解壓 → Claude 補 AI → check.py → push.py
5. **測試 Mont-bell 和 Shopify 通用 extractor**

---

## 五、Extension 已知技術債

| 項目 | 影響 | 
|------|------|
| Mont-bell extractor 未在真實頁面驗證 CSS selector | 可能擷取失敗 |
| Shopify 通用 extractor 未在真實 Shopify 商店驗證 | 同上 |
| converse-tokyo extractor 的 `category_id` 提取邏輯不完整 | product_type 空白 |
| `_body_html` 欄位不在模板中，push.py 可能忽略或報錯 | 需確認 push.py 行為 |
| Extension 無錯誤回報機制（console.warn 只在 DevTools 可見） | debug 困難 |
