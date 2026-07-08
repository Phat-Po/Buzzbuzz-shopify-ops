# BuzzBuzz Chrome Extension — 商品擷取工具

## 安裝

1. 開啟 Chrome，網址列輸入 `chrome://extensions`
2. 開啟右上角「開發人員模式」
3. 點「載入未封裝項目」
4. 選擇 `chrome-extension/` 這個資料夾
5. Extension 應該出現在工具列（橘色蜜蜂圖示）

## 使用

1. 瀏覽到支援的日本品牌商品頁（例如 Converse Tokyo 官網商品頁）
2. 點工具列的 BuzzBuzz icon
3. Popup 自動擷取商品資訊
4. 確認 / 編輯商品類型和售價
5. 點「複製 YAML」或「下載 ZIP」
6. 解壓 ZIP 到 `products/<product-name>/`
7. 用 Claude 補完 AI 區段 → `python scripts/check.py` → 審核 → `python scripts/push.py`

## 支援站台

| 站台 | 擷取方式 |
|------|---------|
| converse-tokyo.jp | 自訂平台（var item_stock + DOM） |
| montbell.com | DOM selectors |
| converse.co.jp | Shopify .json |
| origami-kai-tea.com | Shopify .json |
| humanmade.jp (V2) | Shopify .json |
| katomodels.com (V2) | Shopify .json |
| 其他 Shopify 站 | 自動嘗試 .json |

## 架構

```
popup.html → popup.js      (UI + 匯出)
                ↓
         executeScript()
                ↓
         content.js          (site detection)
         shopify.js          (Shopify .json extractor)
         montbell.js         (Mont-bell DOM extractor)
         brand-map.js        (hostname → brand)
         yaml-builder.js     (data → YAML string)
         image-packer.js     (fetch images → ZIP)
```
