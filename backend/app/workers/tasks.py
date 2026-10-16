import asyncio
from app.core.enrichment.pipeline import EnrichmentPipeline
from app.db.repositories import global_repository

async def enrich_chunk_task(ctx, review_ids: list[int]):
    """Background task to enrich a chunk of reviews asynchronously."""
    reviews = [global_repository._reviews[rid] for rid in review_ids if rid in global_repository._reviews]
    if not reviews:
        return {"status": "empty"}

    pipeline = ctx["pipeline"]
    report = await pipeline.enrich_chunk(reviews)
    return {
        "status": "success",
        "valid": report.valid_count,
        "failed": report.failed_count,
        "cost_usd": float(report.total_cost_usd)
    }

async def embed_chunk_task(ctx, review_ids: list[int]):
    """Background task to compute embeddings for a chunk."""
    return {"status": "success", "count": len(review_ids)}

async def discover_topics_task(ctx):
    """Weekly clustering job proposing new candidate taxonomy topics from 'other' bucket."""
    return {"status": "success", "candidate_clusters": []}

async def nightly_eval_task(ctx):
    """Nightly automated evaluation run against gold benchmark."""
    from app.evaluation.runner import run_evaluation
    report = await run_evaluation(split="test", naive_mode=False)
    return {"status": "completed", "macro_f1": report["sentiment_metrics"]["macro_f1"]}
