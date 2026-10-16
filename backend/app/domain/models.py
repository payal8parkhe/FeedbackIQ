from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field
from app.domain.schemas import Sentiment
from app.domain.taxonomy import TopicSlug

class Review(BaseModel):
    id: int
    org_id: int = 1
    source: str
    external_id: str | None = None
    content_hash: str
    raw_text: str
    clean_text: str
    language: str = "en"
    rating: int | None = Field(default=None, ge=1, le=5)
    created_at: datetime
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"  # pending | enriching | enriched | failed | dead
    attempts: int = 0


class Enrichment(BaseModel):
    review_id: int
    sentiment: Sentiment
    sentiment_score: float | None = None
    topics: list[TopicSlug]
    summary: str
    confidence: float
    model: str
    prompt_version: str
    taxonomy_version: str
    raw_json: dict[str, Any]
    enriched_at: datetime = Field(default_factory=datetime.utcnow)


class SearchHit(BaseModel):
    review_id: int
    source: str
    created_at: datetime
    rating: int | None
    clean_text: str
    summary: str
    sentiment: Sentiment
    topics: list[TopicSlug]
    score: float
    match_type: str  # "vector" | "keyword" | "hybrid_rrf"


class Citation(BaseModel):
    review_id: int
    quoted_text: str | None = None
    confidence: float = 1.0


class GroundedAnswer(BaseModel):
    answer: str
    citations: list[Citation]
    confidence: float
    caveats: list[str] = Field(default_factory=list)
    usage_cost_usd: float = 0.0
    latency_ms: int = 0
    intent: str = "evidence"  # "evidence" | "aggregate" | "unanswerable"
