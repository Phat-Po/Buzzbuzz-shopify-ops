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
7. **標籤**：固定掛 `curated:popo-select` 這一個標籤（標記「Popo 精選」），不用自己編
   brand:/category:/style: 這些——查證後這些細分標籤沒有被 Shopify 官方列為 Agentic
   Storefronts 會同步給 AI 助手的欄位（見 Shopify Help Center: Agentic storefronts
   products），真正保證會被 AI 讀到的是 title/description/options/images/price/
   availability + JSON-LD + metafields，這些才是重點
8. **官方分類**：`shopify_taxonomy_id` 對應 Shopify Standard Product Taxonomy，用
   Admin GraphQL `taxonomy { categories(search: "英文關鍵字") { edges { node { id
   fullName } } } }` 查，找最接近的 fullName 填進去
9. **Collection**：所有產品自動歸進「Popo選物」這個 collection，用 collection ID
   （寫死在 `scripts/push.py` 的 `shopify_default_collection_id`，不是名稱，改名不影響）
10. **URL Handle**：`url_handle` 必填，全英文 ASCII kebab-case，不要用中文標題自動產生
    的 slug（中文 slug 在瀏覽器網址列會變成一長串 %E6%97%A5... 編碼）
11. **分類屬性**：`category_attributes` 選填，push.py 會轉成 `product_taxonomy_value_reference`
    型別 metafield（值是 Shopify TaxonomyValue GID，push.py 自動查，不用自己找），對
    Google Shopping 之類的結構化篩選有幫助。查法見 `products/_template/product.yaml`。
    **已知限制**：這**不是** Admin 商品頁「Category」卡片（Color/Target gender 那些下拉選單）
    實際用的機制——那個卡片是另一套：`shopify` 保留 namespace + `list.metaobject_reference`
    型別，要先用 `standardMetafieldDefinitionEnable` 啟用，但背後的選項值（「Blue」「Female」
    這些）是 Shopify 內部 metaobject，**第三方 app token 查不到也寫不進去**（`metaobjects(type:
    "shopify--color-pattern")` 回空、硬塞值會被拒絕並回「Value require that you select a
    metaobject」）。這是 Shopify 平台限制，不是我們程式碼的問題，已用 CONVERSE TOKYO 實測
    確認，不用重新研究。Category 卡片的下拉選單只能操作者自己在 Admin 手動點選（一個產品
    約 2 分鐘），無法透過 push.py 自動化。`category_attributes` 寫進去的資料仍然有效
    （structured metafield，其他工具讀得到），只是不會顯示在那張卡片裡
12. **SEO Meta 寫法**：善用 160 字上限，型號/賣點/緊迫感都可以寫，但**不要寫確切價格**
    （調價後會過期，SEO snippet 顯示舊價格反而傷信任）

## 工作流

```
① 建立產品資料夾
   mkdir -p products/bao-bao-lucent-m/images
   cp products/_template/product.yaml products/bao-bao-lucent-m/

② 填寫基本欄位（你手動或 Claude 協助）
   品牌、進價、售價、規格、variants（顏色/尺寸，缺貨的選項直接不列進去）
   shopify_taxonomy_id 用 Admin GraphQL 查（見上面「官方分類」說明）
   url_handle 用英文 ASCII slug 填（見上面「URL Handle」說明）
   category_attributes 選填，查法見上面「分類屬性」說明

③ Claude 補完 AI 區段
   標題、描述、SEO、alt text、FAQ、schema
   （tags 固定填 [curated:popo-select]，不用自己編；不寫供應鏈細節、不寫日本原廠
   定價，見 Constraints；seo_meta 善用 160 字上限但不寫確切價格，見上面「SEO Meta
   寫法」；price_gap_note 只供內部分析，不會推送到 Shopify）

④ 質檢
   python scripts/check.py products/bao-bao-lucent-m

⑤ 審核 + 修正

⑥ 推送到 Shopify
   python scripts/push.py products/bao-bao-lucent-m
   實際動作：上傳 images/ 底下的圖片（含 alt text）→ 用 productSet mutation 一次
   建立/更新 title/description/選項(variants)/價格/圖片/官方分類/url_handle →
   寫入一般 metafields（不含 price_gap_note）→ 寫入 category_attributes 分類屬性
   metafields（自動查 TaxonomyValue ID）→ 自動歸進「Popo選物」collection。已經
   published 過的產品重跑這個指令是「更新」（靠 productSet 的 identifier 比對既有
   Shopify ID），不是重複建立一個新產品

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
  操作者的商業機密。**也不寫日本原廠定價**（¥xxx、日幣/日圓xxx、JPY xxx）——會讓人
  反推進貨成本與利潤空間。缺貨的規格選項直接從 variants 移除，不要在文案裡解釋原因。
  顏色/尺寸資訊已經在 variants 結構化欄位裡，description_fact 不用重複寫「目前為XX
  色XX尺寸」。`scripts/check.py` 有自動掃描這類用語，但寫文案時就要避免，不要依賴
  工具兜底。
- **cost_jpy 例外**：`cost_jpy`（日本進價）是唯一允許寫進 Shopify metafields 的成本
  數字（操作者定價時需要對照），但只放 metafield（admin-only，沒有 storefront 存取
  權限），絕對不能出現在任何公開文案欄位裡。

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
  radar/          ← 台灣選品雷達（discovery + validation 兩層驗證方法論）
scripts/          ← CLI 工具
  push.py         ← 發布到 Shopify（DRAFT，含圖片/選項/變體/價格/分類/collection）
  check.py        ← Agent-Ready 質檢
  status.py       ← 查看所有產品狀態
  oauth_setup.py  ← Shopify custom app 一次性授權工具（token 被撤銷才需要重跑）
tasks/            ← 規劃文件
```

## 選品參考
`sourcing/top100.yaml` 包含 100 個精選品項，9 大品類，利潤率 20-80%。
優先操作 Top 20（★★★）：BAO BAO、Porter、Mont-bell、Snow Peak 等。
也可自行指定品牌，不限定於清單內。
