# Handoff：修 push.py 的圖片/變體上傳缺口

> 給下一輪對話的 agent：這份文件是你唯一需要讀的交接資料，讀完照著做就好，不用回頭挖之前的對話。

## 一句話任務

`scripts/push.py` 目前推送產品到 Shopify 時，**完全沒有處理圖片、alt text、變體（顏色/尺寸/價格）**——這些欄位 `product.yaml` 裡都有真實資料，但 `push.py` 沒讀取、沒送出去。第一個試跑產品（CONVERSE TOKYO 10週年限定）已經是 Shopify 上的 DRAFT，但那個 DRAFT **沒有圖、沒有可購買的價格**，只有標題/描述/tags/metafields。你的任務：把這個缺口補上。

## 先驗證這個判斷還成立

```bash
cd "/Volumes/轻松打爆你/VIBE CODING/10_PROJECTS_ACTIVE/20260707__app__buzzbuzz-shopify"
git log --oneline -5
grep -n "images\|variants\|alt_text" scripts/push.py   # 應該完全沒有命中（或你要修的東西已經有人動過）
```

## 需要讀的檔案（照這個順序）

1. `scripts/push.py` — 要改的地方。重點看 `build_product_input()`（目前只送 title/descriptionHtml/productType/vendor/tags/status/seo）和 `push_product()` 主流程（目前只呼叫 `create_product` + `set_metafields`，沒有第三步處理圖片/變體）
2. `products/converse-tokyo-allstar-10th-navy/product.yaml` — 真實資料範例，裡面的 `images`（8張，相對路徑指向同目錄 `images/` 資料夾）、`alt_texts`（每張圖對應的繁中描述）、`variants`（顏色/尺寸選項）、`price_twd` 都是現成、乾淨、已經通過供應鏈保密檢查的資料，可以直接拿來測試
3. `products/_template/product.yaml` — 完整欄位定義與注意事項（含供應鏈保密規則，改文案時要遵守）
4. `AGENTS.md` — 專案治理，尤其是 Constraints 區塊（含這次新加的「供應鏈保密」規則）

## 要做的事（技術方向，不是寫死的步驟，你要自己查 Shopify 最新文件）

Shopify Admin GraphQL API 建立產品的完整流程大致是三段（**確切的 mutation 名稱/參數請自己查 `shopify.dev` 最新文件，不要憑記憶寫，Shopify API 常常改版**）：

1. `productCreate`（現有，已經在跑）——建立產品本體
2. **圖片上傳**：目前的作法通常是先用 `stagedUploadsCreate` 拿到上傳網址，把本地圖片檔案傳上去，再用 `productCreateMedia`（或類似 mutation）把圖片掛到產品上，`alt` 欄位對應 `product.yaml` 的 `alt_texts`
3. **變體（variants）**：用 `productVariantsBulkCreate` 之類的 mutation，把 `product.yaml` 的 `variants`（顏色/尺寸組合）轉成 Shopify variant，每個 variant 要帶上 `price_twd`（換算/直接當 Shopify 售價），否則這個產品在 Shopify 裡沒有可購買的價格

## 已知環境問題（不是這次任務的一部分，但會擋路）

- 這台機器的 `python3` 是 **3.8.1**，但 `pyproject.toml` 宣告 `requires-python = ">=3.12"`——專案沒有真的用 pyproject.toml 建虛擬環境，套件是直接 `pip install` 到全域環境的。這次補了 `pydantic-settings`（`push.py` 原本就依賴，只是環境沒裝）。如果你新加套件，記得也要更新 `pyproject.toml` 的 `dependencies`，並用 `pip install <package>` 直接裝到目前環境（不要假設有 venv）。

## 已經打通、不用重做的東西

- **`.env` 已經有完整、可用的 Shopify 憑證**（`SHOPIFY_STORE`、`SHOPIFY_ADMIN_TOKEN`，是永久有效的 offline access token，不會過期，不用重新走 OAuth）。`.env` 有 `.gitignore`，正常運作不會動到它。
- `scripts/oauth_setup.py` 是取得這組 token 用的一次性工具，正常情況不用再跑；只有 token 被撤銷/重裝 app 時才需要重跑（跑之前要重新走一次 cloudflared 臨時通道流程，過程麻煩，見腳本內註解）。
- `scripts/check.py` 的供應鏈保密自動掃描（第17項檢查）已經生效，之後改任何 `product.yaml` 的文案欄位都會被檢查，不用手動記。

## 驗證方式

1. 改完 `push.py` 後，先跑 `python3 scripts/check.py products/converse-tokyo-allstar-10th-navy` 確認還是 17/17（改 push.py 不該影響這個）
2. **不要對同一個 product.yaml 重跑 `push.py`**——目前的 `push.py` 邏輯是「已發布過就跳過，只能建立新產品，不支援更新」（見 `push_product()` 裡 `if existing_id:` 那段）。要嘛你也順便把「更新已發布產品」的邏輯補上，要嘛先建一個新的測試產品資料夾來驗證圖片/變體上傳有沒有成功
3. 去 Shopify 後台實際打開那個產品（或新測試產品），肉眼確認圖片、alt text、變體、價格都正確顯示

## 這次順便學到、值得記住的教訓

- **同一個網頁上可能同時有「通用參考表」和「這個 SKU 的實際資料」，不能只看表格就當真**——之前把 Converse 官網的尺碼換算表誤當成這雙鞋實際庫存尺碼，鬧了個烏龍，靠操作者對照官網截圖才抓到。改資料時，優先信任明確標記「這個商品規格」的欄位，不要信通用對照表。
- **公開文案（title/description/FAQ/price_gap_note/jsonld）絕對不能寫供應鏈細節**（例如「向官網下單」「官網缺貨」「台灣沒有代理」），這些會被 Shopify metafields 和頁面內容公開，等於告訴別人商業模式。`check.py` 已經有自動掃描守門，但寫文案時就該避免，不要依賴工具兜底。
- **Shopify 2026年起 custom app 的 token 取得方式整個改了**：不再直接顯示 `shpat_` token，改成 Client ID/Secret，要嘛用 client_credentials grant（只能用在免費 development store，付費正式商店會被擋），要嘛走 authorization code grant（需要 redirect URI，適合正式商店，token 永久有效）。如果之後要開新的 Shopify custom app，直接照 `scripts/oauth_setup.py` 的邏輯做，不用重新查一次文件。
