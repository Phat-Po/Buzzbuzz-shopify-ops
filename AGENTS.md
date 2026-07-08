# BuzzBuzz 日本選物店

## Purpose
BuzzBuzz 是面向台灣消費者的日本選物代購 Shopify 商店。這個 repo 是上稿工作台 — 不是 ERP。

核心閉環：**選品 → AI 生成繁中產品頁 → 審核 → 推送到 Shopify → Agent-Ready 質檢**

## Stack
- Python 3.12+ CLI 腳本（無 web 伺服器）
- YAML 檔案儲存（非 SQLite，人可直接讀寫）
- Shopify Admin GraphQL API（產品發布）
- Claude 直接在資料夾中協作編輯（不需要 Claude API key）

## Claude 協作方式

Claude 在這個 repo 中的角色是**文案助手 + 質檢員**：

1. **讀取** `products/<name>/product.yaml` 中的基本欄位
2. **生成**繁中產品內容：標題、三段描述、SEO meta、alt text、FAQ、標籤、JSON-LD schema
3. **直接寫入** product.yaml 的 AI 產出區段
4. **執行** `python scripts/check.py products/<name>` 做 Agent-Ready 質檢
5. **操作者審核後**，執行 `python scripts/push.py products/<name>` 推送到 Shopify

Claude 不透過 API 呼叫 — 而是直接編輯本地檔案，你審核後再推送。

## 台灣市場定位

- **目標市場**：台灣（google.com.tw + Yahoo 台灣）
- **內容語言**：繁體中文（zh-TW）
- **貨幣**：TWD（新台幣）
- **價值主張**：日本好物直送台灣，正品保證，比台灣百貨便宜 30-60%
- **目標客群**：對日本品牌有認知、在意質感和價差的台灣消費者

## Agent-Ready 標準（Shopify Spring '26）

Shopify 2026 年 6 月推出 agentic commerce：產品會自動同步到 ChatGPT、Google Gemini、Microsoft Copilot 等 AI 平台。要讓 BuzzBuzz 產品在 AI 搜尋中被引用，每個產品頁需符合：

1. **標題公式**：`[日本品牌] [商品類型] [關鍵屬性] [差異點] | BuzzBuzz 日本選物`
2. **三段描述**：Fact（規格價差）→ Feel（穿搭場景）→ Trust（正品保證）
3. **結構化 Metafields**：品牌、材質、尺寸、重量、台日價差、日本限定標記
4. **圖片 Alt Text**（繁中）：每張圖都有描述性 alt text
5. **JSON-LD Schema**：Product + Offer(TWD) + Brand + shippingDetails
6. **FAQ ≥3 組**：AI 搜尋特別喜歡引用 FAQ
7. **標籤格式**：`brand:xxx, category:xxx, origin:japan` (namespace:value)

## 工作流

```
① 建立產品資料夾
   mkdir -p products/bao-bao-lucent-m/images
   cp products/_template/product.yaml products/bao-bao-lucent-m/

② 填寫基本欄位（你手動或 Claude 協助）
   品牌、進價、售價、規格...

③ Claude 補完 AI 區段
   標題、描述、SEO、alt text、FAQ、標籤、schema

④ 質檢
   python scripts/check.py products/bao-bao-lucent-m

⑤ 審核 + 修正

⑥ 推送到 Shopify
   python scripts/push.py products/bao-bao-lucent-m

⑦ 查看狀態
   python scripts/status.py
```

## Constraints
- 所有產品預設發布為 **DRAFT**（非 ACTIVE）
- AI 生成的文案必須基於真實產品資訊，不得虛構
- 不得虛構認證、材質、產地、健康功效
- 不得自動建立廣告或爬取競品資料
- **供應鏈保密**：product.yaml 裡所有公開文案欄位（title_zh、description_*、seo_*、
  faq、price_gap_note、jsonld_*）最終會出現在 Shopify 商品頁或 metafields，等於公開
  資訊（含 AI 購物助手讀得到的範圍）。絕對不寫「向官網下單」「官網缺貨/現貨」「台灣
  沒有官方或代理通路」這類洩露進貨來源、庫存監控方式、競業分析結論的句子——這些是
  操作者的商業機密。缺貨的規格選項直接從 variants 移除，不要在文案裡解釋原因。
  `scripts/check.py` 有自動掃描這類用語，但寫文案時就要避免，不要依賴工具兜底。

## Risk Gates（永遠先確認）
- `git push` — 確認後才推送
- Shopify 產品推送 — `push.py` 執行前確認
- `.env` / 憑證變更 — 確認後才修改

## Directory Layout
```
products/         ← 每個產品一個資料夾，內含 product.yaml + images/
  _template/      ← 產品 YAML 模板
sourcing/         ← 選品參考資料
  top100.yaml     ← 2026 台日代購 Top 100 選品清單
scripts/          ← CLI 工具
  push.py         ← 發布到 Shopify（DRAFT）
  check.py        ← Agent-Ready 質檢
  status.py       ← 查看所有產品狀態
tasks/            ← 規劃文件
```

## 選品參考
`sourcing/top100.yaml` 包含 100 個精選品項，9 大品類，利潤率 20-80%。
優先操作 Top 20（★★★）：BAO BAO、Porter、Mont-bell、Snow Peak 等。
也可自行指定品牌，不限定於清單內。
