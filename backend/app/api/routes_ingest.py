import json
import csv
import io
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Depends
from pydantic import BaseModel
from app.api.deps import get_repository, get_enrichment_pipeline
from app.db.repositories import ReviewRepository
from app.core.enrichment.pipeline import EnrichmentPipeline
from app.domain.models import Enrichment

router = APIRouter(prefix="/v1/ingest", tags=["Ingestion"])

class ReviewIngestPayload(BaseModel):
    text: str
    source: str = "api"
    external_id: str | None = None
    rating: int | None = None

class IngestResponse(BaseModel):
    job_id: str
    total_received: int
    new_reviews: int
    duplicates_skipped: int
    message: str

async def process_reviews_background(job_id: str, reviews_to_enrich: list, pipeline: EnrichmentPipeline, repo: ReviewRepository):
    if not reviews_to_enrich:
        repo.update_ingest_job(job_id, done=0, failed=0, state="completed")
        return

    chunk_report = await pipeline.enrich_chunk(reviews_to_enrich, trace_id=f"job-{job_id}")
    
    # Persist enrichments
    for r in reviews_to_enrich:
        if r.id in chunk_report.results:
            enr_data = chunk_report.results[r.id]
            repo.save_enrichment(
                Enrichment(
                    review_id=r.id,
                    sentiment=enr_data.sentiment,
                    topics=enr_data.topics,
                    summary=enr_data.summary,
                    confidence=enr_data.confidence,
                    model=pipeline.model,
                    prompt_version=pipeline.prompt_version,
                    taxonomy_version=pipeline.taxonomy_version,
                    raw_json=enr_data.model_dump()
                )
            )

    # Embed and save vectors
    texts_to_embed = [f"{r.clean_text} {chunk_report.results[r.id].summary}" for r in reviews_to_enrich if r.id in chunk_report.results]
    if texts_to_embed:
        vectors = await pipeline.embedder.embed(texts_to_embed)
        for r, vec in zip(reviews_to_enrich, vectors):
            repo.save_embedding(r.id, vec)

    repo.update_ingest_job(
        job_id,
        done=chunk_report.valid_count,
        failed=chunk_report.failed_count,
        state="completed"
    )

@router.post("", response_model=IngestResponse, status_code=202)
async def ingest_reviews(
    background_tasks: BackgroundTasks,
    file: UploadFile | None = File(default=None),
    payload: list[ReviewIngestPayload] | None = None,
    repo: ReviewRepository = Depends(get_repository),
    pipeline: EnrichmentPipeline = Depends(get_enrichment_pipeline)
):
    raw_items = []

    if file:
        content = await file.read()
        filename = file.filename or ""
        if filename.endswith(".json") or filename.endswith(".jsonl"):
            lines = content.decode("utf-8").splitlines()
            for line in lines:
                line = line.strip()
                if line:
                    try:
                        raw_items.append(json.loads(line))
                    except Exception:
                        pass
        elif filename.endswith(".csv"):
            reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
            for row in reader:
                raw_items.append({
                    "text": row.get("text") or row.get("review") or row.get("body", ""),
                    "source": row.get("source", "csv"),
                    "rating": int(row["rating"]) if row.get("rating") and row["rating"].isdigit() else None
                })
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload CSV or JSON/JSONL.")
    elif payload:
        raw_items = [p.model_dump() for p in payload]
    else:
        raise HTTPException(status_code=400, detail="Must provide either a file or a JSON payload list.")

    if not raw_items:
        raise HTTPException(status_code=400, detail="No valid review records found.")

    new_reviews = []
    duplicates_count = 0

    for idx, item in enumerate(raw_items, start=1):
        text = item.get("text", "")
        if not text:
            continue
        source = item.get("source", "upload")
        rating = item.get("rating")
        review_obj = pipeline.preprocess(raw_text=text, rid=0, source=source, rating=rating)
        inserted_review, is_new = repo.insert_review(review_obj)
        if is_new:
            new_reviews.append(inserted_review)
        else:
            duplicates_count += 1

    job_id = repo.create_ingest_job(total=len(new_reviews))

    # Trigger background enrichment
    background_tasks.add_task(process_reviews_background, job_id, new_reviews, pipeline, repo)

    return IngestResponse(
        job_id=job_id,
        total_received=len(raw_items),
        new_reviews=len(new_reviews),
        duplicates_skipped=duplicates_count,
        message=f"Accepted {len(new_reviews)} new reviews for enrichment. {duplicates_count} duplicates skipped."
    )

@router.get("/{job_id}")
async def get_ingest_progress(job_id: str, repo: ReviewRepository = Depends(get_repository)):
    job = repo.get_ingest_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Ingest job not found.")
    return job
