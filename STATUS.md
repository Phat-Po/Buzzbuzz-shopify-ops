# BuzzBuzz 日本選物店 — Status

## ▲ Current

---

## 2026-07-08 | top100 驗證批次 3 完成（8 品牌），TNF Purple Label A 信號重測修正

**Done this session:**
- 跑完 `top100-validation-sweep-plan.md` 批次 3 的 8 個 ★★★ 品牌全信號驗證：
  HYKE x Porter(17)、Danton(28)、Nanamica(32)、TNF Purple Label(33)、
  Arai 安全帽(51)、Shoei 安全帽(52)、Pokemon Center Japan 限定(70)、
  Traveler's Company(99)
- TNF Purple Label A 信號重測：原關鍵詞「TNF Purple Label」熱度 0 是關鍵詞不匹配，
  改用台灣人實際搜的「紫標」重測 → 56.6（命中），從 2/4 升格 3/4 → 候選
- 結果寫入 `sourcing/radar/candidates.md`，更新 overview 總覽表
- 本批亮點：Shoei 4/4（價差 40-50%，PTT 鄉民背書）、TNF Purple Label 3/4（通路最乾淨，
  台灣完全無官方管道）、Pokemon Center Japan 限定 3/4（日本各地區限定款台北店不進）

**Current state:**
三批累計 24 個 ★★★ 品牌已驗證：可推進 2（Human Made、Mont-bell）、有條件候選 13、
觀察池 9、排除 0。★★★ 剩餘約 14 個（批次 4-5）。觀察池中 HYKE x Porter 和
Traveler's Company 建議不投入資源（niche/客單價太低）。
`sourcing/radar/candidates.md` 和 `tasks/top100-validation-sweep-plan.md` 已同步更新。

**Next steps:**
1. 操作者確認是否繼續批次 4（Issey Miyake Homme Plisse、Snow Peak Apparel、
   KATO/TOMIX 鐵道模型、Medicom Be@rbrick、Tamashii Nations 限定、
   Origami Dripper、Vermicular）
2. 自有物流報價確定後，回頭補所有候選的 D-3 淨利試算

**Decisions / notes:**
- 安全帽品類（Arai/Shoei）信號極強但實務障礙多：體積大運費高、無法試戴、水貨無保固
- TNF Purple Label 是 8 個品牌中通路最乾淨的（台灣完全無官方管道），代購有獨佔性
- Pokemon Center Japan 的代購生態系已極度成熟，需找差異化切入點（目前建議從地區限定
  小物開始）
- 「紫標」關鍵詞教訓：check_trends.py 用的英文詞不一定匹配台灣搜尋習慣，以後驗證
  潮流品牌時應先測台灣慣用的中文簡稱

---

## 2026-07-08 | Category 屬性打通、URL handle/SEO/metafields 收尾

**Done this session:**
- 找到 Shopify Admin 商品頁「Category」卡片（Color/Target gender/Upper material 這些
  下拉選單）的正確 API 寫法：`product_taxonomy_value_reference` 型別 metafield，
  definition 要用 `product_taxonomy_attribute_handle` validation 綁定 taxonomy
  attribute 的 kebab-case handle（例如 `target-gender`），值是 `TaxonomyValue` GID，
  不是文字——這個機制文件不完整，靠 introspection + 試錯才挖出正確格式
- `push.py` 新增 `build_category_attribute_metafields()`：讀 product.yaml 的
  `category_attributes`（人看得懂的 `{Color: Blue, Target gender: Female}` 格式），
  push 時動態查對應 category 的 taxonomy attribute/value，自動轉成正確的 GID 型
  metafield——設計成通用機制，不是寫死 CONVERSE TOKYO 專用
- 建了 4 個對應的 metafield definition 並 pin（color/target_gender/age_group/
  upper_material），CONVERSE TOKYO 已重推驗證：16 個 metafields 全部正確寫入
- 補 `url_handle` 欄位：`productSet` 的 `handle` 之前沒設，Shopify 用中文標題自動產生
  slug，瀏覽器網址列變成一長串 %E6%97%A5... 編碼——現在改用 ASCII slug
  （`converse-tokyo-10th-allstar-j-ox-navy`）
- `price_gap_note` 不再寫進 Shopify metafields（操作者要求，純內部分析欄位），已刪除
  對應的 metafield definition
- CONVERSE TOKYO 的 `seo_meta` 換成強化版（型號+緊迫感），照操作者要求**不寫確切價格**
  （調價後 SERP 顯示舊價格會傷信任）
- Tags 簡化成固定 `curated:popo-select`（上一輪已改 check.py/template，這輪實際重推
  讓 Shopify 上的舊 6 標籤生效替換）

**Current state:**
CONVERSE TOKYO 是目前唯一的真實產品，已完整驗證：8 張圖＋alt text、1 個變體含正確
價格、官方 taxonomy 分類、4 個分類屬性、16 個一般 metafields、ASCII url handle、
單一 curation tag、collection「Popo選物」，全部在 Shopify 上確認過。`push.py`/
`check.py`/`_template/product.yaml` 現在是穩定狀態，下一個新產品照 AGENTS.md 工作流
①-⑦ 走應該不會撞到這些坑。

**Next steps:**
1. 繼續往下跑選品（`sourcing/radar/` 或 `top100-validation-sweep-plan.md`）
2. 下一個新產品建立時，實測一次完整工作流（含 category_attributes/url_handle 這些
   新欄位），確認 AGENTS.md 的說明對得上實際操作

**Decisions / notes:**
- `category_attributes` 的 taxonomy attribute/value 查詢是 push 時動態查的（不是寫死
  在 push.py 裡），換分類或換值都不用改程式碼，只要改 product.yaml
- Tags 對傳統 Google SEO 沒有直接幫助；對 AI agent 的幫助也沒有 Shopify 官方保證
  （官方列出的同步欄位是 title/description/options/images/price/availability，不含
  tags）——固定一個 curation tag 就夠，不用堆疊細分標籤
- `cost_jpy` 允許寫進 Shopify metafields（操作者定價需要），但只放 admin-only
  metafield，絕對不能出現在任何公開文案欄位

## ■ Milestones

- 2026-07-08 push.py 補完圖片/變體上傳（`productSet` 取代已棄用的三段式 mutation）、
  供應鏈保密規則收斂（擋日圓原價）、tags 簡化為單一 curation 標籤 | ✅ done
- 2026-07-08 選品雷達上線（`sourcing/radar/` discovery+validation 兩層方法論）+ 打通 Shopify OAuth（`scripts/oauth_setup.py`）+ 第一個產品（CONVERSE TOKYO）成功推送 Shopify DRAFT | ✅ done
- 2026-07-07 項目重新定位：從 ERP 改為本地 CLI 上稿工具，建立 products/YAML 模板、三個 CLI 腳本、Top100 選品清單 | ✅ done

## ▼ Archive

- 2026-07-07 MVP-0: FastAPI + SQLite web dashboard (已廢棄，保留在 git history)
