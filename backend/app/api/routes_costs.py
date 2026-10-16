from fastapi import APIRouter
from app.core.observability.usage_log import global_usage_logger

router = APIRouter(prefix="/v1/costs", tags=["Cost & Observability"])

@router.get("/summary")
async def get_cost_summary():
    """Retrieve spend by purpose, token counts, and recent LLM audit logs."""
    return global_usage_logger.get_summary()
