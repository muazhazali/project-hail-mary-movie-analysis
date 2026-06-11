"""Search routers using Qdrant for semantic search."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SubtitleLine
from app.services.embedding import embed_query
from app.services.qdrant_service import search_similar
from app.schemas import SearchQuery, SearchResult

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("/semantic")
def semantic_search(
    q: str,
    limit: int = 10,
    speaker: str | None = None,
    db: Session = Depends(get_db),
):
    """Semantic search using Qdrant vector similarity."""
    if not q or len(q.strip()) < 1:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    query_embedding = embed_query(q.strip())
    
    # Search in Qdrant
    qdrant_results = search_similar(
        query_vector=query_embedding,
        limit=limit,
        speaker=speaker,
    )
    
    # Get idx values from Qdrant results
    idxs = [r["id"] for r in qdrant_results]
    
    if not idxs:
        return {"query": q, "results": []}
    
    # Fetch full records from PostgreSQL
    subtitle_lines = db.query(SubtitleLine).filter(SubtitleLine.idx.in_(idxs)).all()
    
    # Create lookup by idx for ordering
    lines_by_idx = {line.idx: line for line in subtitle_lines}
    
    results = []
    for qr in qdrant_results:
        idx = qr["id"]
        line = lines_by_idx.get(idx)
        if line:
            results.append(SearchResult(
                idx=line.idx,
                start_time=line.start_time,
                end_time=line.end_time,
                raw_text=line.raw_text,
                clean_text=line.clean_text,
                speaker=line.speaker,
                similarity=round(qr["score"], 4),  # Qdrant returns cosine similarity directly
                sentiment_compound=line.sentiment_compound,
            ))
    
    return {"query": q, "results": results}


@router.get("/text")
def text_search(
    q: str,
    limit: int = 10,
    speaker: str | None = None,
    db: Session = Depends(get_db),
):
    """Text/keyword search using PostgreSQL ILIKE."""
    if not q or len(q.strip()) < 1:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    pattern = f"%{q.strip()}%"
    query = (
        db.query(
            SubtitleLine.idx,
            SubtitleLine.start_time,
            SubtitleLine.end_time,
            SubtitleLine.raw_text,
            SubtitleLine.clean_text,
            SubtitleLine.speaker,
            SubtitleLine.sentiment_compound,
        )
        .filter(SubtitleLine.clean_text.ilike(pattern))
    )
    if speaker:
        query = query.filter(SubtitleLine.speaker == speaker)
    rows = query.order_by(SubtitleLine.idx).limit(limit).all()
    
    results = [
        SearchResult(
            idx=r.idx,
            start_time=r.start_time,
            end_time=r.end_time,
            raw_text=r.raw_text,
            clean_text=r.clean_text,
            speaker=r.speaker,
            similarity=None,
            sentiment_compound=r.sentiment_compound,
        )
        for r in rows
    ]
    return {"query": q, "results": results}
