from datetime import datetime
from app.core.retrieval.fusion import reciprocal_rank_fusion
from app.domain.models import SearchHit
from app.domain.schemas import Sentiment
from app.domain.taxonomy import TopicSlug

def make_hit(rid: int, score: float) -> SearchHit:
    return SearchHit(
        review_id=rid,
        source="appstore",
        created_at=datetime.utcnow(),
        rating=5,
        clean_text=f"Review text {rid}",
        summary=f"Summary {rid}",
        sentiment=Sentiment.positive,
        topics=[TopicSlug.LOGIN_AUTH],
        score=score,
        match_type="vector"
    )

def test_rrf_combines_and_boosts_overlap():
    v_hits = [make_hit(1, 0.9), make_hit(2, 0.8), make_hit(3, 0.7)]
    k_hits = [make_hit(2, 5.0), make_hit(4, 4.0), make_hit(1, 3.0)]

    fused = reciprocal_rank_fusion(v_hits, k_hits, k=60, top_n=5)
    fused_ids = [h.review_id for h in fused]

    # Item 2 is rank 2 in vector and rank 1 in keyword -> should have highest combined RRF
    assert fused[0].review_id == 2
    # All 4 unique items should be present
    assert set(fused_ids) == {1, 2, 3, 4}
