from fastapi import APIRouter, Depends
from app.api.deps import get_repository
from app.db.repositories import ReviewRepository
from app.core.qa.aggregates import compute_topic_aggregates

router = APIRouter(prefix="/v1/insights", tags=["Insights"])

@router.get("/topics")
async def get_topic_insights(repo: ReviewRepository = Depends(get_repository)):
    all_docs = repo.get_all_enriched_for_retrieval()
    return compute_topic_aggregates(all_docs)
