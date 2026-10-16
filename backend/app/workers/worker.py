import asyncio
from app.workers.tasks import enrich_chunk_task, embed_chunk_task, discover_topics_task, nightly_eval_task
from app.api.deps import get_enrichment_pipeline

async def startup(ctx):
    ctx["pipeline"] = get_enrichment_pipeline()
    print("[FeedbackIQ Worker] Worker initialized and ready for jobs.")

async def shutdown(ctx):
    print("[FeedbackIQ Worker] Worker shutting down cleanly.")

class WorkerSettings:
    functions = [enrich_chunk_task, embed_chunk_task, discover_topics_task, nightly_eval_task]
    on_startup = startup
    on_shutdown = shutdown

if __name__ == "__main__":
    print("[FeedbackIQ Worker] Starting background runner...")
    asyncio.run(startup({}))
