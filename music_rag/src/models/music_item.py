"""Data models for music items and metadata."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class MusicMetadata(BaseModel):
    """Metadata for a music track."""

    genre: Optional[str] = None
    subgenre: Optional[str] = None
    cultural_origin: Optional[str] = None
    tempo: Optional[float] = None  # BPM
    key: Optional[str] = None
    time_signature: Optional[str] = None
    instrumentation: List[str] = Field(default_factory=list)
    mood: List[str] = Field(default_factory=list)
    era: Optional[str] = None
    duration: Optional[float] = None  # seconds
    is_live_performance: bool = False
    venue: Optional[str] = None
    audience_response: Optional[str] = None
    lyrics: Optional[str] = None


class MusicItem(BaseModel):
    """Represents a music track with embeddings and metadata."""

    id: str
    title: str
    artist: str
    description: Optional[str] = None
    audio_path: Optional[str] = None
    text_embedding: Optional[List[float]] = None
    audio_embedding: Optional[List[float]] = None
    metadata: MusicMetadata = Field(default_factory=MusicMetadata)
    created_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class QueryResult(BaseModel):
    """Result from a retrieval query."""

    music_item: MusicItem
    score: float
    retrieval_type: str  # 'broad', 'targeted', 'hybrid'


class RetrievalQuery(BaseModel):
    """Query parameters for music retrieval."""

    text_query: Optional[str] = None
    audio_path: Optional[str] = None
    top_k: int = Field(default=10, ge=1, le=100)

    # Metadata filters
    genre_filter: Optional[List[str]] = None
    mood_filter: Optional[List[str]] = None
    tempo_range: Optional[tuple[float, float]] = None
    cultural_origin_filter: Optional[List[str]] = None

    # Retrieval strategy
    use_broad_retrieval: bool = True
    use_targeted_retrieval: bool = True
    semantic_weight: float = Field(default=0.7, ge=0.0, le=1.0)
