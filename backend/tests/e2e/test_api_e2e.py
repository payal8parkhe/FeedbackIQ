import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.repositories import global_repository
from app.domain.models import Review, Enrichment
from app.domain.schemas import Sentiment
from app.domain.taxonomy import TopicSlug
from datetime import datetime

client = TestClient(app)

@pytest.fixture(autouse=True)
def seed_sample_reviews():
    repo = global_repository
    # Ensure at least 3 reviews exist
    for i in range(1, 4):
        r = Review(
            id=i,
            source="appstore",
            content_hash=f"hash-{i}",
            raw_text=f"Sample feedback text {i}",
            clean_text=f"Sample feedback text {i}",
            rating=5,
            created_at=datetime.utcnow(),
            status="enriched"
        )
        repo.insert_review(r)
        repo.save_enrichment(Enrichment(
            review_id=i,
            sentiment=Sentiment.positive,
            topics=[TopicSlug.LOGIN_AUTH],
            summary=f"Sample summary for review {i}",
            confidence=0.95,
            model="gpt-4o-mini",
            prompt_version="v1",
            taxonomy_version="v1",
            raw_json={}
        ))
        repo.save_embedding(i, [0.01 * (i + j) for j in range(1024)])


def test_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_list_reviews():
    response = client.get("/v1/reviews")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 1


def test_search_endpoint():
    payload = {"query": "sample feedback", "mode": "hybrid", "k": 5}
    response = client.post("/v1/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "hybrid"
    assert "hits" in data
    assert len(data["hits"]) >= 1


def test_ask_endpoint():
    payload = {"question": "What feedback was provided?"}
    response = client.post("/v1/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "citations" in data


def test_insights_topics():
    response = client.get("/v1/insights/topics")
    assert response.status_code == 200
    data = response.json()
    assert "top_topics" in data
    assert "sentiment_distribution" in data


def test_prometheus_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "llm_request_seconds" in response.text
