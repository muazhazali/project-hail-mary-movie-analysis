# Agent Instructions

## Package Managers (Critical)
- **Python**: Use `uv`, not pip. Lockfile is `backend/uv.lock`.
- **Node**: Use `pnpm`, not npm. Lockfile is `frontend/pnpm-lock.yaml`.

## Environment Setup
- **Create `.env` at repo root** (NOT in backend/ or frontend/):
  ```
  DB_HOST=localhost
  DB_PORT=5432
  DB_USER=postgres
  DB_PASS=<password>
  DB_NAME=postgres
  APP_ENV=development
  CORS_ORIGINS=http://localhost:5173,http://localhost:3000
  EMBEDDING_MODEL=all-MiniLM-L6-v2
  
  # Qdrant settings (choose local OR cloud)
  # Local Qdrant:
  QDRANT_HOST=localhost
  QDRANT_PORT=6333
  
  # Cloud Qdrant (optional):
  QDRANT_URL=https://your-cluster.qdrant.io
  QDRANT_API_KEY=your-api-key
  ```
- `backend/app/config.py` auto-loads `../.env` from repo root.

## Database Prerequisites
- **PostgreSQL 16** for structured data (lines, speakers, stats).
- **Qdrant** for vector embeddings (semantic search).
- Start via Docker: `docker compose up db qdrant -d`
- Backend auto-creates PostgreSQL tables and Qdrant collection on startup.

## Development Commands

### Backend (from `backend/`)
```bash
# Install deps
uv sync --dev

# Run dev server
uv run -- uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# One-time seed (parses SRT, computes embeddings, populates PostgreSQL + Qdrant)
# WARNING: Requires spaCy model (en_core_web_sm) and sentence-transformers
uv run -- python app/scripts/seed.py

# Run tests (requires seeded database)
uv run --dev pytest tests/test_api.py -v
```

### Frontend (from `frontend/`)
```bash
pnpm install
pnpm run dev    # port 5173
```

## API & Routing
- All backend routes are under `/api/*` prefix.
- Vite dev server proxies `/api` → `http://localhost:8000` automatically.
- Frontend uses React Router + Recharts.

## Testing Gotchas
- Tests assume database is seeded with subtitle data.
- Tests set `APP_ENV=test` internally but still hit the real DB.
- Tests look for known speakers: Mary, Grace, Ryland, Stratt, Rocky.

## Data Files
- Subtitle SRT expected at `data/Project.Hail.Mary.2026.*.srt`.
- `seed.py` skips ingestion if both PostgreSQL has data AND Qdrant has vectors.

## Build/Deploy
- Backend Dockerfile uses `uv` for production.
- Frontend builds to `dist/` for nginx/Caddy serving.
- docker-compose.yml includes db + qdrant + backend; frontend commented out for dev.

## Architecture Notes
- **PostgreSQL**: Stores subtitle lines, speaker stats, metadata.
- **Qdrant**: Stores 384-dimensional embeddings for semantic search.
- **Hybrid Search**: Semantic search queries Qdrant for similar vectors, then fetches full records from PostgreSQL by idx.
- pgvector has been removed - embeddings are now stored exclusively in Qdrant.
