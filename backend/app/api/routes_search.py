import time
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Any
from app.api.deps import get_repository, get_embedder
from app.db.repositories import ReviewRepository
from app.core.embeddings.base import Embedder
from app.core.retrieval.vector import vector_search
from app.core.retrieval.keyword import keyword_search
from app.core.retrieval.fusion import reciprocal_rank_fusion
from app.domain.models import SearchHit

router = APIRouter(prefix="/v1/search", tags=["Search"])

class SearchRequest(BaseModel):
    query: str
    mode: str = "hybrid"  # "hybrid" | "vector" | "keyword"
    k: int = 15
    filters: dict[str, Any] = {}

class SearchResponse(BaseModel):
    query: str
    mode: str
    total_hits: int
    latency_ms: int
    hits: list[SearchHit]

@router.post("", response_model=SearchResponse)
async def search_reviews(
    req: SearchRequest,
    repo: ReviewRepository = Depends(get_repository),
    embedder: Embedder = Depends(get_embedder)
):
    start = time.perf_counter()
    all_docs = repo.get_all_enriched_for_retrieval()

    if req.mode == "vector":
        query_vec = (await embedder.embed([req.query]))[0]
        hits = vector_search(query_vec, all_docs, top_k=req.k, filters=req.filters)
    elif req.mode == "keyword":
        hits = keyword_search(req.query, all_docs, top_k=req.k, filters=req.filters)
    else:  # hybrid RRF
        query_vec = (await embedder.embed([req.query]))[0]
        v_hits = vector_search(query_vec, all_docs, top_k=30, filters=req.filters)
        k_hits = keyword_search(req.query, all_docs, top_k=30, filters=req.filters)
        hits = reciprocal_rank_fusion(v_hits, k_hits, k=60, top_n=req.k)

    elapsed_ms = int((time.perf_counter() - start) * 1000)

    return SearchResponse(
        query=req.query,
        mode=req.mode,
        total_hits=len(hits),
        latency_ms=elapsed_ms,
        hits=hits
    )
