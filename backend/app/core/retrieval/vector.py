import math
from typing import Any
from app.domain.models import SearchHit

def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    dot = sum(x * y for x, y in zip(v1, v2))
    norm1 = math.sqrt(sum(x * x for x in v1))
    norm2 = math.sqrt(sum(y * y for y in v2))
    return (dot / (norm1 * norm2)) if (norm1 > 0 and norm2 > 0) else 0.0


def vector_search(
    query_vec: list[float],
    reviews_with_vectors: list[dict[str, Any]],
    top_k: int = 30,
    filters: dict[str, Any] | None = None
) -> list[SearchHit]:
    """In-memory cosine similarity vector search with metadata filters."""
    hits = []
    filters = filters or {}

    for item in reviews_with_vectors:
        # Check metadata filters
        if "sentiment" in filters and item["sentiment"] != filters["sentiment"]:
            continue
        if "topic" in filters and filters["topic"] not in item["topics"]:
            continue
        if "rating" in filters and item.get("rating") != filters["rating"]:
            continue
        if "source" in filters and item.get("source") != filters["source"]:
            continue

        sim = cosine_similarity(query_vec, item["embedding"])
        hits.append((sim, item))

    hits.sort(key=lambda x: x[0], reverse=True)

    results = []
    for score, item in hits[:top_k]:
        results.append(
            SearchHit(
                review_id=item["id"],
                source=item.get("source", "appstore"),
                created_at=item["created_at"],
                rating=item.get("rating"),
                clean_text=item["clean_text"],
                summary=item.get("summary", ""),
                sentiment=item["sentiment"],
                topics=item["topics"],
                score=round(score, 4),
                match_type="vector"
            )
        )
    return results
