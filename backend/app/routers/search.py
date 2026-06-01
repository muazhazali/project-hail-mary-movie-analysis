import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.models import SubtitleLine
from app.services.embedding import embed_query
from app.schemas import SearchQuery, SearchResult

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("/semantic")
def semantic_search(
    q: str,
    limit: int = 10,
    speaker: str | None = None,
    db: Session = Depends(get_db),
):
    if not q or len(q.strip()) < 1:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    query_embedding = embed_query(q.strip())
    # pgvector cosine similarity operator <=> (1 - cosine_distance)
    # We want top by cosine similarity, so order by embedding <=> query_embedding
    # pgvector <=> returns cosine distance, so smaller = more similar.
    speaker_filter = ""
    params = {"embedding": json.dumps(query_embedding), "limit": limit}
    if speaker:
        speaker_filter = " AND speaker = :speaker"
        params["speaker"] = speaker
    
    sql = f"""
        SELECT idx, start_time, end_time, raw_text, clean_text, speaker,
               sentiment_compound,
               embedding <=> (:embedding)::vector AS distance
        FROM subtitle_lines
        WHERE embedding IS NOT NULL {speaker_filter}
        ORDER BY embedding <=> (:embedding)::vector ASC
        LIMIT :limit
    """
    rows = db.execute(text(sql), params).mappings().all()
    
    results = []
    for row in rows:
        # convert distance to similarity (1 - distance for cosine)
        similarity = 1.0 - float(row["distance"])
        results.append(SearchResult(
            idx=row["idx"],
            start_time=row["start_time"],
            end_time=row["end_time"],
            raw_text=row["raw_text"],
            clean_text=row["clean_text"],
            speaker=row["speaker"],
            similarity=round(similarity, 4),
            sentiment_compound=row["sentiment_compound"],
        ))
    return {"query": q, "results": results}


@router.get("/text")
def text_search(
    q: str,
    limit: int = 10,
    speaker: str | None = None,
    db: Session = Depends(get_db),
):
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
