import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine, Base
from app.routers import subtitles, search, analytics
from app.services.qdrant_service import ensure_collection

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create PostgreSQL tables and ensure Qdrant collection
    Base.metadata.create_all(bind=engine)
    ensure_collection()
    yield
    # Shutdown: nothing special


app = FastAPI(
    title="Project Hail Mary Subtitle Analysis",
    description="NLP + vector semantic search dashboard for movie subtitles",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(subtitles.router)
app.include_router(search.router)
app.include_router(analytics.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.datetime.utcnow().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
