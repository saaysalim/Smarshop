# SmartShop

SmartShop is a runnable multi-boutique demo storefront with a React/TypeScript
frontend, a FastAPI backend, and PostgreSQL for Docker-based runs. It includes
catalogue search and filters, demo catalogue synchronisation, a shopping bag,
and database-backed demo orders with stock checks.

## GitHub Pages catalogue preview

The GitHub Pages workflow publishes a static sample catalogue at
`https://saaysalim.github.io/Smarshop/`. In repository **Settings → Pages**,
set the source to **GitHub Actions**. The workflow runs on pushes to `main` and
can also be run manually from the Actions tab.

GitHub Pages cannot run the Python API or database. The preview supports
search and boutique/stock filters, but its data is a static sample and
shopping, checkout, and synchronisation are disabled. The full application
remains available using the local setup below.

To build the preview locally, run `python backend/export_preview.py` from the
repository root, then set `VITE_CATALOGUE_PREVIEW=true` and run
`npm run build` in `frontend/`. Set `VITE_BASE_PATH=/Smarshop/` when building
for this repository's GitHub Pages URL.

## Run with Docker Compose

Requirements: Docker Desktop (or Docker Engine with Compose).

1. Copy `.env.example` to `.env`.
2. Replace the placeholder `POSTGRES_PASSWORD` with a private alphanumeric
   password.
3. From this directory, run:

   ```bash
   docker compose up --build
   ```

Open the storefront at http://localhost:5173. The API docs are at
http://localhost:8000/docs and its health endpoint is
http://localhost:8000/api/health.

On Windows PowerShell, copy the environment file with:

```powershell
Copy-Item .env.example .env
```

## Run locally without Docker

The backend defaults to SQLite when `DATABASE_URL` is unset. In one terminal:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

In another terminal:

```powershell
cd frontend
npm ci
npm run dev
```

The storefront expects the API at `http://localhost:8000` by default. Override
this with `VITE_API_URL` when running the frontend against another API URL.

## Test the backend

With the backend requirements installed, run from `backend/`:

```powershell
pytest
```

Tests use an isolated SQLite database and do not require Docker or PostgreSQL.

## API

- `GET /api/health` — database readiness
- `GET /api/boutiques` — available boutiques and integration type
- `GET /api/products?q=bag` — search product names
- `GET /api/products?boutique_id=1` — filter by boutique
- `GET /api/products?stock_only=true` — show in-stock products
- `POST /api/admin/boutiques/{id}/catalogue-sync` — synchronise a demo catalogue
- `POST /api/orders` — place an order and decrement available stock

The demo adapters return deterministic sample products. Order records retain
product names and prices as they were at checkout. The checkout does not collect
personal details or process payments.

## Scope and deployment

This is a development demo, not a production commerce system. User accounts,
real payment processing, delivery, and parcel tracking are not implemented.
Catalogue synchronisation is not protected by administrator authentication.
Do not expose this deployment publicly without adding appropriate security,
authentication, and production configuration.
