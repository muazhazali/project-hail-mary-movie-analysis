# Project Hail Mary — Subtitle Intelligence Dashboard

NLP + vector semantic search dashboard that ingests a movie subtitle (SRT) file, computes sentiment, word stats, speaker analytics, and vector embeddings — then lets you explore and search everything through a sci-fi themed React dashboard backed by FastAPI and PostgreSQL with pgvector.

---

## Tech Stack

- **Backend (Python / uv)**: FastAPI, SQLAlchemy 2.0, Pydantic 2.x, psycopg2, pgvector, sentence-transformers, spaCy, VADER
- **Frontend (Node / pnpm)**: React 18, Vite, Tailwind CSS, Recharts, React Router
- **Database**: PostgreSQL 16 with the **pgvector** extension

---

## Prerequisites

- **Python** (3.11+)
- **uv** (install: https://docs.astral.sh/uv/getting-started/installation/)
- **Node** (v20+)
- **pnpm** (install: `corepack enable && corepack prepare pnpm --activate`, or via npm: `npm install -g pnpm`)
- **PostgreSQL** (local dev) or a remote Postgres with **pgvector** enabled

---

## Project Layout

```
├── backend/
│   ├── app/
│   │   ├── main.py                          # FastAPI entry point
│   │   ├── config.py                        # Pydantic settings (env vars)
│   │   ├── database.py                      # SQLAlchemy engine / session
│   │   ├── models.py                         # DB tables
│   │   ├── schemas.py                        # Pydantic request/response models
│   │   ├── routers/
│   │   │   ├── subtitles.py                  # Lines, speakers, timeline
│   │   │   ├── search.py                     # Semantic + text search
│   │   │   └── analytics.py                  # Top words, sentiment, duration
│   │   ├── services/
│   │   │   ├── srt_parser.py                 # SRT → structured data
│   │   │   ├── nlp.py                        # Sentiment, NER, word stats
│   │   │   └── embedding.py                  # Sentence-transformers → vectors
│   │   └── scripts/
│   │       └── seed.py                       # Ingest the SRT once
│   ├── pyproject.toml                        # UV dependency manifest
│   ├── uv.lock                               # Reproducible lockfile
│   └── Dockerfile                            # Production image via uv
├── frontend/
│   ├── src/
│   │   ├── App.jsx / api.js                  # Routing & API client
│   │   ├── pages/
│   │   │   ├── Overview.jsx                  # Stats + sentiment pie + word cloud
│   │   │   ├── TimelinePage.jsx            # Sentiment / WPM over time
│   │   │   ├── SpeakersPage.jsx              # Stats + lines per character
│   │   │   ├── SearchPage.jsx                # Semantic & keyword search
│   │   │   └── ExplorerPage.jsx              # Infinite-scroll subtitle viewer
│   │   └── index.css                         # Tailwind + custom space theme
│   ├── package.json
│   ├── pnpm-lock.yaml                        # Reproducible pnpm lock
│   ├── tailwind.config.js / postcss.config.js
│   ├── vite.config.js
│   └── Dockerfile                            # Production nginx image
├── data/
│   └── Project.Hail.Mary.2026.*.srt          # Subtitle source file
├── .env                                      # DB credentials & settings
└── docker-compose.yml                        # Postgres + backend containers
```

---

## Configuration

Create a `.env` in the **repo root**. Example:

```bash
# Database
DB_HOST=192.168.1.108
DB_PORT=5432
DB_USER=postgres
DB_PASS=Muazoreo123
DB_NAME=postgres

# Backend
APP_ENV=development
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

`backend/app/config.py` auto-loads `../.env` from the repo root so running `uv run` from the backend directory still finds it.

---

## Local Development

### 1. Start the database (optional — if you don't have a remote Postgres)

```bash
docker compose up db -d
```

This spins up `pgvector/pgvector:pg16` on port `5432`. Make sure your `.env` points to it.

### 2. Backend setup

```bash
cd backend

# uv creates backend/.venv automatically
uv sync --dev

# (Optional) If working from a fresh database, seed subtitles + embeddings
uv run -- python app/scripts/seed.py

# Start the FastAPI dev server
uv run -- uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend will be available at http://localhost:8000.

### 3. Frontend setup

In a new terminal:

```bash
cd frontend
pnpm install
pnpm run dev
```

Frontend will be available at http://localhost:5173.  
The Vite proxy config (`/api` → `http://localhost:8000`) handles dev API calls automatically.

### 4. (Optional) Run backend tests

```bash
cd backend
uv run --dev pytest tests/test_api.py -v
```

---

## Production / Proxmox LXC Deployment

### Docker images

Build once, then push or `docker save` + transfer to your LXC.

#### Backend image

```bash
cd backend
docker build -t hail-mary-backend:latest .
```

#### Frontend image

```bash
cd frontend
docker build -t hail-mary-frontend:latest .
```

### Docker Compose (production style)

You can uncomment the `frontend` service and remove dev-only parts to deploy all three services:

```yaml
# docker-compose.yml
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASS}
      POSTGRES_DB: ${DB_NAME}
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 5s
      timeout: 5s
      retries: 10

  backend:
    build: ./backend
    env_file:
      - .env
    environment:
      - APP_ENV=production
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    command:
      - "uv"
      - "run"
      - "--no-dev"
      - "uvicorn"
      - "app.main:app"
      - "--host"
      - "0.0.0.0"
      - "--port"
      - "8000"

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  pgdata:
```

Deploy:

```bash
# On your Proxmox LXC (assuming Docker/Compose installed)
docker compose up -d
```

### Or: manual LXC (no Docker)

If you want to run the backend directly inside the LXC:

```bash
# Inside LXC
cd /opt/project-hail-mary-movie-analysis/backend
uv sync --no-dev

# Start as a systemd service or in a tmux/screen session
uv run --no-dev uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Serve frontend static files with **Caddy** or **nginx**:

```bash
cd /opt/project-hail-mary-movie-analysis/frontend
pnpm install
pnpm run build
# Copy dist/ to your web server root (e.g. /var/www/html)
```

A minimal Caddyfile example:

```
:80 {
    root * /var/www/html
    file_server
    reverse_proxy /api/* localhost:8000
}
```

---

## Environment variables reference

| Variable         | Default                              | Description                          |
|------------------|--------------------------------------|--------------------------------------|
| `DB_HOST`        | `localhost`                            | Postgres host                        |
| `DB_PORT`        | `5432`                                 | Postgres port                        |
| `DB_USER`        | `postgres`                             | Postgres user                        |
| `DB_PASS`        | `postgres`                             | Postgres password                    |
| `DB_NAME`        | `postgres`                             | Postgres database                    |
| `APP_ENV`        | `development`                          | FastAPI / SQLAlchemy debug toggle    |
| `CORS_ORIGINS`   | `http://localhost:5173,...`          | Allowed frontend origins             |
| `EMBEDDING_MODEL`| `all-MiniLM-L6-v2`                     | Sentence-transformers model name     |

---

## Features

- **SRT Ingest**: parses subtitle entries, cleans HTML / speaker cues / sound effects, classifies line types.
- **Sentiment Analysis**: VADER compound/pos/neu/neg scores per line.
- **Named Entity Extraction**: spaCy NER across all dialogue.
- **Speaker Stats**: lines, words, unique vocabulary, average sentiment, average WPM, top entities.
- **Vector Embeddings**: sentence-transformers `all-MiniLM-L6-v2` → 384-dimensional vectors stored in pgvector.
- **Semantic Search**: query any natural language phrase; get top-k similar subtitle lines via pgvector cosine distance.
- **Keyword Search**: exact `ILIKE` full-text search fallback.
- **Interactive Dashboard**:
  - Overview: total lines, word count, speakers, average sentiment, sentiment pie chart, top-word cloud.
  - Timeline: line chart of sentiment, words/min, and word density over time, filterable by speaker.
  - Speakers: ranked speaker stats + dialogue excerpts.
  - Search: semantic vs keyword modes with speaker filtering.
  - Explorer: infinite-scroll subtitle transcript with sentiment bars.

---

## License

MIT
