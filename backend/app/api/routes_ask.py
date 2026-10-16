from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Any
from app.api.deps import get_repository, get_embedder, get_answer_service
from app.db.repositories import ReviewRepository
from app.core.embeddings.base import Embedder
from app.core.qa.answer import AnswerService
from app.core.qa.router import QueryRouter
from app.core.qa.aggregates import compute_topic_aggregates
from app.core.retrieval.vector import vector_search
from app.core.retrieval.keyword import keyword_search
from app.core.retrieval.fusion import reciprocal_rank_fusion
from app.domain.models import GroundedAnswer

router = APIRouter(prefix="/v1/ask", tags=["Q&A"])
query_router = QueryRouter()

class AskRequest(BaseModel):
    question: str
    filters: dict[str, Any] = {}

@router.post("", response_model=GroundedAnswer)
async def ask_question(
    req: AskRequest,
    repo: ReviewRepository = Depends(get_repository),
    embedder: Embedder = Depends(get_embedder),
    answer_svc: AnswerService = Depends(get_answer_service)
):
    intent = query_router.route(req.question)

    if intent == "unanswerable":
        return GroundedAnswer(
            answer="This question is outside the scope of customer feedback. FeedbackIQ answers questions strictly supported by real customer reviews.",
            citations=[],
            confidence=1.0,
            intent="unanswerable"
        )

    all_docs = repo.get_all_enriched_for_retrieval()

    # If aggregate question ("What are customers complaining about?"), run SQL group-by
    sql_summary_text = None
    if intent == "aggregate":
        agg_data = compute_topic_aggregates(all_docs)
        top_str = "\n".join([f"- {t['topic']}: {t['count']} reviews ({t['percentage']}%)" for t in agg_data["top_topics"][:6]])
        sql_summary_text = f"Total Reviews Analyzed: {agg_data['total_reviews']}\nTop Complaint Topics:\n{top_str}"

    # Retrieve evidence reviews via Hybrid RRF
    query_vec = (await embedder.embed([req.question]))[0]
    v_hits = vector_search(query_vec, all_docs, top_k=20, filters=req.filters)
    k_hits = keyword_search(req.question, all_docs, top_k=20, filters=req.filters)
    fused_hits = reciprocal_rank_fusion(v_hits, k_hits, k=60, top_n=8)

    answer = await answer_svc.answer_question(
        question=req.question,
        context_reviews=fused_hits,
        sql_aggregates=sql_summary_text,
        trace_id="ask-api"
    )
    answer.intent = intent
    return answer
