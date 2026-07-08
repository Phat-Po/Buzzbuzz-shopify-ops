# BuzzBuzz Shopify 上稿工具

## Purpose
用 Claude Code / Codex 把產品推送到 Shopify 的命令列工具。

## Stack
- Python 3.12+ CLI 腳本
- Shopify Admin GraphQL API
- Claude Code / Codex 協作

## Scripts

| Script | 功能 |
|--------|------|
| `push.py` | 發布產品到 Shopify（DRAFT） |
| `check.py` | 檢查產品資料完整性 |
| `status.py` | 查看所有產品狀態 |
| `oauth_setup.py` | Shopify 一次性授權設定 |

## Quick Start

詳見 `tasks/shopify-sop.html`（內部 SOP 簡報）。

## Risk Gates
- `git push` — 確認後才推送
- Shopify 產品推送 — `push.py` 執行前確認
- `.env` / 憑證變更 — 確認後才修改
