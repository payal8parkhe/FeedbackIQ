from collections import Counter
from typing import Any

def compute_topic_aggregates(reviews: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Computes exact topic counts, sentiment distributions, and sample review quotes.
    Solves the classic RAG limitation where top-k retrieval cannot count.
    """
    total = len(reviews)
    if total == 0:
        return {"total": 0, "topics": {}, "sentiment": {}}

    topic_counter = Counter()
    sentiment_counter = Counter()
    topic_samples: dict[str, list[dict[str, Any]]] = {}

    for r in reviews:
        sentiment_counter[r.get("sentiment", "neutral")] += 1
        for t in r.get("topics", []):
            topic_slug = str(t)
            topic_counter[topic_slug] += 1
            if topic_slug not in topic_samples:
                topic_samples[topic_slug] = []
            if len(topic_samples[topic_slug]) < 3:
                topic_samples[topic_slug].append({
                    "id": r["id"],
                    "rating": r.get("rating"),
                    "text": r["clean_text"][:120] + "..." if len(r["clean_text"]) > 120 else r["clean_text"]
                })

    top_topics = [
        {
            "topic": topic,
            "count": count,
            "percentage": round((count / total) * 100, 1),
            "samples": topic_samples.get(topic, [])
        }
        for topic, count in topic_counter.most_common(10)
    ]

    return {
        "total_reviews": total,
        "sentiment_distribution": dict(sentiment_counter),
        "top_topics": top_topics
    }
