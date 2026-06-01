import datetime
import os

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import engine, Base, SessionLocal
from app.routers import subtitles, search, analytics

settings = get_settings()

# Create tables on startup
Base.metadata.create_all(bind=engine)

# Ensure pgvector extension exists
with SessionLocal() as db:
    db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    db.commit()

app = FastAPI(
    title="Project Hail Mary Subtitle Analysis",
    description="NLP + vector semantic search dashboard for movie subtitles",
    version="0.1.0",
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
