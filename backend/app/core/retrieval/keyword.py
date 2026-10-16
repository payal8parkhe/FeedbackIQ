import re
from typing import Any
from app.domain.models import SearchHit

def keyword_search(
    query: str,
    reviews: list[dict[str, Any]],
    top_k: int = 30,
    filters: dict[str, Any] | None = None
) -> list[SearchHit]:
    """Token-based lexical matching search with frequency and title scoring."""
    tokens = [t.lower() for t in re.findall(r"\w+", query) if len(t) > 2]
    if not tokens:
        return []

    filters = filters or {}
    hits = []

    for item in reviews:
        # Check metadata filters
        if "sentiment" in filters and item["sentiment"] != filters["sentiment"]:
            continue
        if "topic" in filters and filters["topic"] not in item["topics"]:
            continue
        if "rating" in filters and item.get("rating") != filters["rating"]:
            continue
        if "source" in filters and item.get("source") != filters["source"]:
            continue

        text_lower = item["clean_text"].lower()
        score = sum(text_lower.count(tok) for tok in tokens)
        
        # Boost if matches topic or summary
        for topic in item.get("topics", []):
            if any(tok in str(topic).lower() for tok in tokens):
                score += 3
        
        if score > 0:
            hits.append((score, item))

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
                score=float(score),
                match_type="keyword"
            )
        )
    return results
