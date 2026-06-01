from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import SubtitleLine

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/top-words")
def top_words(speaker: str | None = None, limit: int = 50, db: Session = Depends(get_db)):
    """Return most common words across all dialogue lines."""
    query = db.query(SubtitleLine).filter(SubtitleLine.line_type == "dialogue")
    if speaker:
        query = query.filter(SubtitleLine.speaker == speaker)
    rows = query.all()
    
    from collections import Counter
    import re
    counter = Counter()
    stopwords = {
        "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your",
        "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she",
        "her", "hers", "herself", "it", "its", "itself", "they", "them", "their",
        "theirs", "themselves", "what", "which", "who", "whom", "this", "that",
        "these", "those", "am", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an",
        "the", "and", "but", "if", "or", "because", "as", "until", "while", "of",
        "at", "by", "for", "with", "through", "during", "before", "after", "above",
        "below", "up", "down", "in", "out", "on", "off", "over", "under", "again",
        "further", "then", "once", "here", "there", "when", "where", "why", "how",
        "all", "any", "both", "each", "few", "more", "most", "other", "some",
        "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too",
        "very", "s", "t", "can", "will", "just", "don", "should", "now", "d",
        "ll", "m", "o", "re", "ve", "y", "ain", "aren", "couldn", "didn", "doesn",
        "hadn", "hasn", "haven", "isn", "ma", "mightn", "mustn", "needn", "shan",
        "shouldn", "wasn", "weren", "won", "wouldn", "to", "from",
    }
    for row in rows:
        words = re.findall(r"\b\w+\b", row.clean_text.lower())
        for w in words:
            if w not in stopwords and len(w) > 2:
                counter[w] += 1
    return [{"word": w, "count": c} for w, c in counter.most_common(limit)]


@router.get("/sentiment-distribution")
def sentiment_distribution(db: Session = Depends(get_db)):
    """Bucket sentiment scores into ranges."""
    rows = db.query(SubtitleLine.sentiment_compound).filter(
        SubtitleLine.sentiment_compound.isnot(None),
        SubtitleLine.line_type == "dialogue",
    ).all()
    buckets = {
        "very_negative": 0,
        "negative": 0,
        "neutral": 0,
        "positive": 0,
        "very_positive": 0,
    }
    for (val,) in rows:
        if val <= -0.5:
            buckets["very_negative"] += 1
        elif val <= -0.1:
            buckets["negative"] += 1
        elif val <= 0.1:
            buckets["neutral"] += 1
        elif val <= 0.5:
            buckets["positive"] += 1
        else:
            buckets["very_positive"] += 1
    return buckets


@router.get("/duration-stats")
def duration_stats(db: Session = Depends(get_db)):
    """Basic duration statistics."""
    max_end = db.query(func.max(SubtitleLine.end_time)).scalar() or 0.0
    total_dialogue = db.query(func.sum(SubtitleLine.duration)).scalar() or 0.0
    return {
        "runtime_seconds": round(max_end, 2),
        "runtime_human": _human_time(max_end),
        "total_dialogue_seconds": round(total_dialogue, 2),
        "total_dialogue_human": _human_time(total_dialogue),
    }


def _human_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"
