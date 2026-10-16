import time
import uuid
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from pathlib import Path

from app.config import settings
import app.core.observability.metrics  # registers custom Prometheus metrics
from app.api.routes_ingest import router as ingest_router
from app.api.routes_reviews import router as reviews_router
from app.api.routes_search import router as search_router
from app.api.routes_ask import router as ask_router
from app.api.routes_insights import router as insights_router
from app.api.routes_eval import router as eval_router
from app.api.routes_costs import router as costs_router

app = FastAPI(
    title="FeedbackIQ API",
    version="0.1.0",
    description="Enterprise AI Customer Feedback Intelligence Platform with Schema-Validated Enrichment, Hybrid RAG, and Cost/Latency Observability",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# Enable CORS for local Next.js / React dev servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request tracing and timing middleware
@app.middleware("http")
async def trace_and_timing_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-Id", f"trace-{uuid.uuid4().hex[:8]}")
    request.state.trace_id = trace_id
    start_time = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = int((time.perf_counter() - start_time) * 1000)
    response.headers["X-Trace-Id"] = trace_id
    response.headers["X-Response-Time-Ms"] = str(elapsed_ms)
    return response

# Prometheus metrics endpoint
@app.get("/metrics", tags=["Ops"])
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Health & Readiness checks
@app.get("/healthz", tags=["Ops"])
async def healthz():
    return {"status": "ok", "app": "FeedbackIQ", "environment": settings.ENVIRONMENT}

@app.get("/readyz", tags=["Ops"])
async def readyz():
    return {"status": "ready", "llm_provider": settings.LLM_PROVIDER, "model": settings.ENRICH_MODEL}

# Mount API Routers
app.include_router(ingest_router)
app.include_router(reviews_router)
app.include_router(search_router)
app.include_router(ask_router)
app.include_router(insights_router)
app.include_router(eval_router)
app.include_router(costs_router)

# Mount frontend web dashboard if static index.html exists
frontend_index = Path(__file__).resolve().parent.parent.parent / "frontend" / "public" / "index.html"
if frontend_index.exists():
    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def serve_dashboard():
        return HTMLResponse(content=frontend_index.read_text(encoding="utf-8"))
else:
    @app.get("/", include_in_schema=False)
    async def root_redirect():
        return {"app": "FeedbackIQ", "docs": "/docs", "status": "running"}
