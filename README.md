# BuzzBuzz 日本選物店

面向台灣消費者的日本選物代購 Shopify 商店。這個 repo 是上稿工作台 — 非 ERP，非 web dashboard。

## 工作流

```
選品 → 建立產品 YAML → Claude 生成繁中內容 → 質檢 → 推送到 Shopify
```

## 目錄

```
products/         ← 每個產品一個資料夾（product.yaml + images/）
sourcing/         ← 選品參考（Top 100 清單）
scripts/          ← CLI 工具
  push.py         ← 發布到 Shopify
  check.py        ← Agent-Ready 質檢
  status.py       ← 查看所有產品狀態
```

## 快速開始

```bash
cd 20260707__app__buzzbuzz-shopify
cp .env.example .env        # 填寫 Shopify 憑證
pip install -e .

# 查看選品參考
cat sourcing/top100.yaml

# 建立新產品
cp -r products/_template products/你的產品名
# 編輯 products/你的產品名/product.yaml

# 讓 Claude 幫你補完繁中內容（直接在對話中說）
# 「幫我把 products/xxx/product.yaml 的 AI 區段寫完」

# 質檢
python scripts/check.py products/你的產品名

# 推送到 Shopify（草稿）
python scripts/push.py products/你的產品名

# 查看所有產品狀態
python scripts/status.py
```

## Agent-Ready 標準

每個產品頁同時服務人類消費者和 AI agent（Shopify Catalog API、ChatGPT、Google AI Overviews）。
詳見 `AGENTS.md` 和 `products/_template/product.yaml` 中的欄位說明。
