from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.deps import get_repository
from app.db.repositories import ReviewRepository

router = APIRouter(prefix="/v1/reviews", tags=["Reviews"])

@router.get("")
async def list_reviews(
    sentiment: str | None = Query(default=None, description="Filter by sentiment: positive, negative, neutral, mixed"),
    topic: str | None = Query(default=None, description="Filter by topic slug"),
    rating: int | None = Query(default=None, ge=1, le=5, description="Filter by star rating"),
    source: str | None = Query(default=None, description="Filter by source"),
    status: str | None = Query(default=None, description="Filter by status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    repo: ReviewRepository = Depends(get_repository)
):
    reviews = repo.list_reviews(
        sentiment=sentiment,
        topic=topic,
        rating=rating,
        source=source,
        status=status,
        limit=limit,
        offset=offset
    )
    return {
        "items": reviews,
        "count": len(reviews),
        "limit": limit,
        "offset": offset
    }

@router.get("/{review_id}")
async def get_review(review_id: int, repo: ReviewRepository = Depends(get_repository)):
    review = repo.get_review(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review
