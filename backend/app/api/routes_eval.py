import json
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from app.evaluation.runner import run_evaluation

router = APIRouter(prefix="/v1/eval", tags=["Evaluation"])

class EvalTriggerRequest(BaseModel):
    split: str = "dev"
    batched: bool = False
    max_items: int | None = 30

@router.post("/run")
async def trigger_eval(req: EvalTriggerRequest):
    """Trigger an evaluation run against the gold set."""
    report = await run_evaluation(
        split=req.split,
        naive_mode=not req.batched,
        max_items=req.max_items
    )
    return {
        "status": "completed",
        "split": req.split,
        "sample_size": report["sample_size"],
        "sentiment_macro_f1": report["sentiment_metrics"]["macro_f1"],
        "sentiment_accuracy": report["sentiment_metrics"]["accuracy"],
        "topic_micro_f1": report["topic_metrics"]["micro_f1"],
        "schema_valid_rate": report["schema_reliability"]["schema_valid_rate"],
        "cost_per_1k_usd": report["cost_and_latency"]["cost_per_1k_usd"],
        "report": report
    }

@router.get("/runs")
async def list_eval_runs():
    """Retrieve stored baseline evaluation report."""
    base_path = Path(__file__).resolve().parent.parent / "evaluation" / "gold" / "baseline_report.json"
    if not base_path.exists():
        return {"runs": [], "message": "No eval run recorded yet. Run POST /v1/eval/run to benchmark."}
    with open(base_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {"latest_run": data}
