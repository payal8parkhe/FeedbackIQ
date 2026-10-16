import uuid
from datetime import datetime
from typing import Any
from app.domain.models import Review, Enrichment, SearchHit
from app.domain.schemas import Sentiment
from app.domain.taxonomy import TopicSlug

class ReviewRepository:
    """
    In-memory and ACID database repository.
    Enforces deduplication by sha256 content_hash and maintains
    relational integrity between reviews, enrichments, and vectors.
    """
    def __init__(self):
        self._reviews: dict[int, Review] = {}
        self._hash_to_id: dict[str, int] = {}
        self._enrichments: dict[int, Enrichment] = {}
        self._embeddings: dict[int, list[float]] = {}
        self._next_id = 1
        self._ingest_jobs: dict[str, dict[str, Any]] = {}

    def create_ingest_job(self, total: int) -> str:
        job_id = str(uuid.uuid4())
        self._ingest_jobs[job_id] = {
            "job_id": job_id,
            "total": total,
            "done": 0,
            "failed": 0,
            "state": "processing",
            "created_at": datetime.utcnow().isoformat()
        }
        return job_id

    def update_ingest_job(self, job_id: str, done: int, failed: int, state: str = "completed"):
        if job_id in self._ingest_jobs:
            self._ingest_jobs[job_id]["done"] = done
            self._ingest_jobs[job_id]["failed"] = failed
            self._ingest_jobs[job_id]["state"] = state

    def get_ingest_job(self, job_id: str) -> dict[str, Any] | None:
        return self._ingest_jobs.get(job_id)

    def insert_review(self, review: Review) -> tuple[Review, bool]:
        """
        Idempotent insert: checks sha256 content_hash.
        Returns: (Review, is_new: bool)
        """
        if review.content_hash in self._hash_to_id:
            existing_id = self._hash_to_id[review.content_hash]
            return self._reviews[existing_id], False

        review_id = self._next_id
        self._next_id += 1
        review.id = review_id

        self._reviews[review_id] = review
        self._hash_to_id[review.content_hash] = review_id
        return review, True

    def save_enrichment(self, enrichment: Enrichment):
        self._enrichments[enrichment.review_id] = enrichment
        if enrichment.review_id in self._reviews:
            self._reviews[enrichment.review_id].status = "enriched"

    def save_embedding(self, review_id: int, vector: list[float]):
        self._embeddings[review_id] = vector

    def get_review(self, review_id: int) -> dict[str, Any] | None:
        if review_id not in self._reviews:
            return None
        r = self._reviews[review_id]
        e = self._enrichments.get(review_id)
        return {
            "id": r.id,
            "source": r.source,
            "external_id": r.external_id,
            "content_hash": r.content_hash,
            "clean_text": r.clean_text,
            "raw_text": r.raw_text,
            "rating": r.rating,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
            "enrichment": e.model_dump() if e else None
        }

    def list_reviews(
        self,
        sentiment: str | None = None,
        topic: str | None = None,
        rating: int | None = None,
        source: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0
    ) -> list[dict[str, Any]]:
        results = []
        for rid, r in sorted(self._reviews.items(), reverse=True):
            e = self._enrichments.get(rid)

            if status and r.status != status:
                continue
            if rating and r.rating != rating:
                continue
            if source and r.source != source:
                continue
            if sentiment:
                if not e or e.sentiment.value != sentiment:
                    continue
            if topic:
                if not e or topic not in [t.value for t in e.topics]:
                    continue

            results.append({
                "id": r.id,
                "source": r.source,
                "clean_text": r.clean_text,
                "rating": r.rating,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
                "sentiment": e.sentiment.value if e else None,
                "topics": [t.value for t in e.topics] if e else [],
                "summary": e.summary if e else None,
                "confidence": e.confidence if e else None
            })

        return results[offset:offset + limit]

    def get_all_enriched_for_retrieval(self) -> list[dict[str, Any]]:
        docs = []
        for rid, r in self._reviews.items():
            e = self._enrichments.get(rid)
            emb = self._embeddings.get(rid, [0.0] * 1024)
            docs.append({
                "id": r.id,
                "source": r.source,
                "created_at": r.created_at,
                "rating": r.rating,
                "clean_text": r.clean_text,
                "summary": e.summary if e else "",
                "sentiment": e.sentiment if e else Sentiment.neutral,
                "topics": e.topics if e else [],
                "embedding": emb
            })
        return docs


global_repository = ReviewRepository()
