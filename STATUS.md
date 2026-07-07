# BuzzBuzz 日本選物店 — Status

## ▲ Current

---

## 2026-07-07 | 項目重新定位：從 ERP 改為本地 CLI 上稿工具

**Done this session:**
- 項目從 `shopify-launch-os` rename 到 `buzzbuzz-shopify`
- Claude session history 已遷移（relocate-claude-sessions.sh）
- 舊代碼全清（FastAPI、SQLAlchemy、Jinja2、SQLite、所有 routes/models/schemas/services/templates）
- 新目錄結構建立（products/_template/、sourcing/）
- 產品 YAML 模板：`products/_template/product.yaml`（覆蓋 agent-ready 所有欄位）
- Top 100 選品清單：`sourcing/top100.yaml`（9 大品類結構化）
- 三個 CLI 腳本：
  - `scripts/push.py` — 讀取 YAML → Shopify GraphQL API → 建立草稿產品 + metafields
  - `scripts/check.py` — Agent-Ready 質檢（16 項檢查清單）
  - `scripts/status.py` — 掃描所有產品狀態
- AGENTS.md 重寫：BuzzBuzz 定位 + Claude 協作方式 + Agent-Ready 標準
- .env.example 精簡（僅 Shopify 憑證）
- .gitignore 更新
- pyproject.toml 精簡（僅 httpx + pyyaml + pydantic-settings）
- README.md 重寫

**Current state:**
項目已從 web ERP 改造為本地 CLI 上稿工具。所有檔案都在本地，Claude 可直接編輯 YAML，無需 API 呼叫。Shopify push 腳本待真實憑證後測試。

**Next steps:**
1. 設定 Shopify 憑證到 .env
2. 建立第一個真實產品（從 Top 100 選一個品牌）
3. Claude 補完 product.yaml 的 AI 區段（繁中內容）
4. `python scripts/check.py` 質檢
5. `python scripts/push.py` 推送測試

**Decisions / notes:**
- 不使用資料庫 — YAML 檔案即記錄，人可直接讀寫編輯
- 不使用 Claude API — Claude 在 repo 中直接協作
- 產品預設發布為 DRAFT（非 ACTIVE）
- 目標市場：台灣（繁中內容、TWD 計價、google.com.tw SEO）
- Agent-Ready 標準對齊 Shopify Spring '26（agentic commerce）

## ■ Milestones

_(empty)_

## ▼ Archive

- 2026-07-07 MVP-0: FastAPI + SQLite web dashboard (已廢棄，保留在 git history)
