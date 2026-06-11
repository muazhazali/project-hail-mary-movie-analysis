import datetime
from typing import Optional

from sqlalchemy import Integer, String, Float, DateTime, Text, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SubtitleLine(Base):
    __tablename__ = "subtitle_lines"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    idx: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    start_time: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    duration: Mapped[float] = mapped_column(Float, nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    clean_text: Mapped[str] = mapped_column(Text, nullable=False)
    line_type: Mapped[str] = mapped_column(String(32), nullable=False, default="dialogue")
    speaker: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    sentiment_compound: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sentiment_pos: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sentiment_neu: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sentiment_neg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    words_per_minute: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # Embeddings now stored in Qdrant (not PostgreSQL)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    __table_args__ = (
        Index("ix_subtitle_lines_start_end", "start_time", "end_time"),
    )


class SpeakerStat(Base):
    __tablename__ = "speaker_stats"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    speaker: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    line_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unique_word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_sentiment: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_wpm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    top_entities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
