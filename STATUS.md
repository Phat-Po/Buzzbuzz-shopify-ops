# Shopify Product Launch OS — Status

## ▲ Current

---

## 2026-07-07 | MVP-0 foundation built

**Done this session:**
- Project scaffold with full governance (AGENTS.md, CLAUDE.md, README.md, .gitignore)
- SQLite database with 7 tables (products, variants, images, listing_copies, seo_scores, publish_logs, readiness_checks)
- Product CRUD via both JSON API and web forms
- CSV/JSON import
- Status pipeline with enforced transition gates (IDEA → SOURCED requires cost_price, MATERIAL_READY requires image + notes)
- Web dashboard showing products grouped by pipeline status with missing-field indicators
- Product detail page with status bar, pricing, variants, images, and advance controls
- Image upload to local storage
- Sample seed script with 5 realistic product candidates
- Dark/light theme CSS

**Current state:**
MVP-0 is complete and working. Server runs at localhost:8000. All CRUD, import, pipeline advancement, and dashboard views tested and verified. 8 test products in DB (5 seeded + 2 CSV import + 1 API creation).

**Next steps:**
1. MVP-1: Add Claude API integration for AI listing generation
2. MVP-1: Listing copy versioning with approve/reject/regenerate
3. MVP-1: SEO scoring engine (15 checks)

**Decisions / notes:**
- Used Python 3.12 + FastAPI + SQLite (not Next.js/Supabase — simpler for single-user pipeline tool)
- Starlette 1.3 TemplateResponse API: signature is (request, name, context), not the old (name, {request: ...})
- htmx 2.0.4 vendored locally (no CDN)

## ■ Milestones

_(empty)_

## ▼ Archive

_(empty)_
