# Shopify Product Launch OS

## Purpose
Local-first tool for managing the full product lifecycle: sourcing, AI listing generation, SEO review, Shopify publishing, and platform readiness checks. Built for a solo cross-border ecommerce operator.

## Stack
- Python 3.12+ / FastAPI / SQLAlchemy 2.0
- SQLite (local file database)
- Jinja2 templates + htmx (no build step)
- Claude API (AI listing generation)
- Shopify Admin GraphQL API (publishing)

## Constraints
- Single store only (no multi-store)
- Products always publish as DRAFT — never ACTIVE by default
- AI-generated copy must trace to operator-provided source data
- No fabricated claims (health, safety, certifications, materials)
- No automatic ad creation or product scraping

## Risk Gates (always confirm)
- `git push`
- Shopify product creation/update (confirmation screen required)
- Any destructive database operation
- `.env` / credential changes

## Directory Layout
```
app/           — FastAPI application code
data/          — SQLite DB + uploaded media (gitignored)
scripts/       — utility scripts
tasks/         — planning artifacts
tests/         — pytest test suite
```

## Status Pipeline
IDEA → SOURCED → MATERIAL_READY → AI_COPY_GENERATED → SEO_REVIEWED → READY_TO_PUBLISH → PUBLISHED_DRAFT → LIVE → TRACKING
