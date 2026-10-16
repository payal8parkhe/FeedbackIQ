import math
from typing import Any
from app.domain.models import SearchHit

def reciprocal_rank_fusion(
    vector_hits: list[SearchHit],
    keyword_hits: list[SearchHit],
    k: int = 60,
    top_n: int = 30
) -> list[SearchHit]:
    """
    Reciprocal Rank Fusion (RRF):
    RRF(d) = sum_{r in {vector, keyword}} 1 / (k + rank_r(d))
    k = 60 default
    """
    rrf_scores: dict[int, float] = {}
    hit_map: dict[int, SearchHit] = {}

    for rank, hit in enumerate(vector_hits, start=1):
        rrf_scores[hit.review_id] = rrf_scores.get(hit.review_id, 0.0) + (1.0 / (k + rank))
        hit_map[hit.review_id] = hit

    for rank, hit in enumerate(keyword_hits, start=1):
        rrf_scores[hit.review_id] = rrf_scores.get(hit.review_id, 0.0) + (1.0 / (k + rank))
        if hit.review_id not in hit_map:
            hit_map[hit.review_id] = hit

    # Sort descending by RRF score
    sorted_ids = sorted(rrf_scores.keys(), key=lambda rid: rrf_scores[rid], reverse=True)

    results = []
    for rid in sorted_ids[:top_n]:
        orig = hit_map[rid]
        results.append(
            SearchHit(
                review_id=orig.review_id,
                source=orig.source,
                created_at=orig.created_at,
                rating=orig.rating,
                clean_text=orig.clean_text,
                summary=orig.summary,
                sentiment=orig.sentiment,
                topics=orig.topics,
                score=round(rrf_scores[rid], 6),
                match_type="hybrid_rrf"
            )
        )
    return results


def maximal_marginal_relevance(
    query_vec: list[float],
    candidate_hits: list[tuple[SearchHit, list[float]]],
    top_k: int = 8,
    lambda_param: float = 0.7
) -> list[SearchHit]:
    """
    MMR: picks items maximizing lambda * sim(d, q) - (1 - lambda) * max_sim(d, selected)
    Prevents near-identical reviews from filling the context window.
    """
    def cosine_sim(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        return (dot / (norm_a * norm_b)) if (norm_a > 0 and norm_b > 0) else 0.0

    if not candidate_hits:
        return []

    selected: list[tuple[SearchHit, list[float]]] = []
    candidates = list(candidate_hits)

    while len(selected) < min(top_k, len(candidate_hits)) and candidates:
        best_score = -float("inf")
        best_idx = -1

        for i, (hit, vec) in enumerate(candidates):
            sim_q = cosine_sim(vec, query_vec)
            if not selected:
                mmr_score = sim_q
            else:
                max_sim_selected = max(cosine_sim(vec, sel_vec) for _, sel_vec in selected)
                mmr_score = lambda_param * sim_q - (1.0 - lambda_param) * max_sim_selected

            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = i

        selected.append(candidates.pop(best_idx))

    return [hit for hit, _ in selected]
