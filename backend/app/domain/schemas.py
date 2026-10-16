from enum import Enum
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from app.domain.taxonomy import TopicSlug

class Sentiment(str, Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"
    mixed = "mixed"


SummaryText = Annotated[str, StringConstraints(min_length=10, max_length=300, strip_whitespace=True)]

class ReviewEnrichment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    review_id: int = Field(..., description="Echoed back review ID to prevent misalignment")
    sentiment: Sentiment = Field(..., description="Textual sentiment of the review")
    topics: list[TopicSlug] = Field(..., min_length=1, max_length=5, description="1 to 5 taxonomy slugs")
    summary: SummaryText = Field(..., description="1 to 2 sentence summary of core message")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence score (0.0 to 1.0)")


class BatchEnrichment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[ReviewEnrichment]


class SingleReviewEnrichmentResponse(BaseModel):
    sentiment: Sentiment
    topics: list[TopicSlug]
    summary: str
    confidence: float
    model: str
    prompt_version: str
    taxonomy_version: str
