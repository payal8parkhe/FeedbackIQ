#!/usr/bin/env python3
"""
Seed FeedbackIQ with realistic reviews and enrichments for instant live demo.
"""
import asyncio
import json
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.db.repositories import global_repository
from app.api.deps import get_enrichment_pipeline
from app.domain.models import Enrichment

async def seed_data(count: int = 50):
    root = Path(__file__).resolve().parent.parent
    gold_path = root / "backend" / "app" / "evaluation" / "gold" / "gold_reviews.jsonl"
    
    if not gold_path.exists():
        print("Gold reviews not found. Running build_gold_set.py first...")
        from scripts.build_gold_set import main as build_gold
        build_gold()

    pipeline = get_enrichment_pipeline()
    repo = global_repository

    reviews = []
    with open(gold_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                reviews.append(json.loads(line))
            if len(reviews) >= count:
                break

    print(f"Seeding {len(reviews)} reviews into FeedbackIQ repository...")
    prepped = []
    for item in reviews:
        r = pipeline.preprocess(
            raw_text=item["text"],
            rid=0,
            source=item.get("source", "appstore"),
            rating=item.get("rating")
        )
        saved_r, is_new = repo.insert_review(r)
        prepped.append(saved_r)

    print(f"Enriching reviews with model '{pipeline.model}'...")
    chunk_report = await pipeline.enrich_chunk(prepped)
    
    for r in prepped:
        if r.id in chunk_report.results:
            enr = chunk_report.results[r.id]
            repo.save_enrichment(
                Enrichment(
                    review_id=r.id,
                    sentiment=enr.sentiment,
                    topics=enr.topics,
                    summary=enr.summary,
                    confidence=enr.confidence,
                    model=pipeline.model,
                    prompt_version=pipeline.prompt_version,
                    taxonomy_version=pipeline.taxonomy_version,
                    raw_json=enr.model_dump()
                )
            )

    print(f"Computing 1024-dim retrieval embeddings for {len(prepped)} reviews...")
    texts = [f"{r.clean_text} {chunk_report.results[r.id].summary}" for r in prepped if r.id in chunk_report.results]
    embeddings = await pipeline.embedder.embed(texts)
    for r, vec in zip(prepped, embeddings):
        repo.save_embedding(r.id, vec)

    print(f"Successfully seeded {chunk_report.valid_count} enriched reviews!")
    print(f"  Valid items: {chunk_report.valid_count}")
    print(f"  Estimated cost: ${chunk_report.total_cost_usd:.6f}")
    print(f"  Elapsed time: {chunk_report.elapsed_ms} ms")

if __name__ == "__main__":
    asyncio.run(seed_data(60))
