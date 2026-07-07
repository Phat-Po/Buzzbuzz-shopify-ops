# Shopify Product Launch OS

Local-first product launch management for solo Shopify operators. Manage product candidates, generate AI-powered listing copy, review SEO quality, and publish to Shopify — all from a single dashboard.

## Quick Start

```bash
cd 20260707__app__shopify-launch-os
cp .env.example .env        # fill in your keys
pip install -e .
python -m app.main
```

Open http://localhost:8000 in your browser.

## Features (MVP-0)

- Product candidate CRUD with web dashboard
- CSV/JSON bulk import
- Image upload and management
- Status pipeline with enforced transition gates
- Dashboard with products grouped by status
