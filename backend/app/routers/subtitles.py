from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import SubtitleLine, SpeakerStat
from app.schemas import SubtitleLineOut, SpeakerStatOut, TimelinePoint

router = APIRouter(prefix="/api/subtitles", tags=["subtitles"])


@router.get("/lines", response_model=list[SubtitleLineOut])
def list_lines(
    skip: int = 0,
    limit: int = 100,
    speaker: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(SubtitleLine).order_by(SubtitleLine.idx)
    if speaker:
        query = query.filter(SubtitleLine.speaker == speaker)
    return query.offset(skip).limit(limit).all()


@router.get("/lines/{idx}", response_model=SubtitleLineOut)
def get_line(idx: int, db: Session = Depends(get_db)):
    line = db.query(SubtitleLine).filter(SubtitleLine.idx == idx).first()
    if not line:
        raise HTTPException(status_code=404, detail="Line not found")
    return line


@router.get("/speakers", response_model=list[SpeakerStatOut])
def list_speakers(db: Session = Depends(get_db)):
    return db.query(SpeakerStat).order_by(SpeakerStat.line_count.desc()).all()


@router.get("/speakers/{speaker}", response_model=SpeakerStatOut)
def get_speaker(speaker: str, db: Session = Depends(get_db)):
    stat = db.query(SpeakerStat).filter(SpeakerStat.speaker == speaker).first()
    if not stat:
        raise HTTPException(status_code=404, detail="Speaker not found")
    return stat


@router.get("/timeline", response_model=list[TimelinePoint])
def timeline(
    speaker: str | None = None,
    window: int = 60,
    db: Session = Depends(get_db),
):
    """Return timeline aggregated into time windows (seconds)."""
    query = db.query(SubtitleLine)
    if speaker:
        query = query.filter(SubtitleLine.speaker == speaker)
    lines = query.order_by(SubtitleLine.start_time).all()
    
    if not lines:
        return []
    
    buckets = {}
    for line in lines:
        bucket = int(line.start_time // window) * window
        if bucket not in buckets:
            buckets[bucket] = {
                "sentiments": [],
                "wpms": [],
                "word_count": 0,
            }
        if line.sentiment_compound is not None:
            buckets[bucket]["sentiments"].append(line.sentiment_compound)
        if line.words_per_minute is not None:
            buckets[bucket]["wpms"].append(line.words_per_minute)
        buckets[bucket]["word_count"] += line.word_count
    
    points = []
    for bucket in sorted(buckets.keys()):
        b = buckets[bucket]
        points.append(TimelinePoint(
            start_time=bucket,
            sentiment=sum(b["sentiments"]) / len(b["sentiments"]) if b["sentiments"] else None,
            wpm=sum(b["wpms"]) / len(b["wpms"]) if b["wpms"] else None,
            word_count=b["word_count"],
        ))
    return points


@router.get("/stats")
def global_stats(db: Session = Depends(get_db)):
    total_lines = db.query(SubtitleLine).count()
    total_words = db.query(func.sum(SubtitleLine.word_count)).scalar() or 0
    avg_sent = db.query(func.avg(SubtitleLine.sentiment_compound)).scalar()
    unique_speakers = db.query(func.count(SpeakerStat.id)).scalar()
    line_type_counts = (
        db.query(SubtitleLine.line_type, func.count(SubtitleLine.id))
        .group_by(SubtitleLine.line_type)
        .all()
    )
    return {
        "total_lines": total_lines,
        "total_words": int(total_words),
        "avg_sentiment": float(avg_sent) if avg_sent is not None else None,
        "unique_speakers": int(unique_speakers),
        "line_type_counts": {lt: int(cnt) for lt, cnt in line_type_counts},
    }
