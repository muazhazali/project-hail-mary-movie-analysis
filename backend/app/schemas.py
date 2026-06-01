from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SubtitleLineIn(BaseModel):
    idx: int
    start_time: float
    end_time: float
    raw_text: str
    clean_text: str
    line_type: str = "dialogue"
    speaker: Optional[str] = None
    sentiment_compound: Optional[float] = None
    word_count: int = 0
    words_per_minute: Optional[float] = None
    duration: float


class SubtitleLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    idx: int
    start_time: float
    end_time: float
    duration: float
    raw_text: str
    clean_text: str
    line_type: str
    speaker: Optional[str] = None
    sentiment_compound: Optional[float] = None
    word_count: int
    words_per_minute: Optional[float] = None
    created_at: Optional[datetime] = None


class SpeakerStatOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    speaker: str
    line_count: int
    word_count: int
    unique_word_count: int
    avg_sentiment: Optional[float] = None
    avg_wpm: Optional[float] = None
    top_entities: Optional[str] = None


class SearchQuery(BaseModel):
    q: str
    limit: int = 10
    speaker: Optional[str] = None


class SearchResult(BaseModel):
    idx: int
    start_time: float
    end_time: float
    raw_text: str
    clean_text: str
    speaker: Optional[str] = None
    similarity: Optional[float] = None
    sentiment_compound: Optional[float] = None


class TimelinePoint(BaseModel):
    start_time: float
    sentiment: Optional[float] = None
    wpm: Optional[float] = None
    word_count: int
