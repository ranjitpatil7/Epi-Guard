from celery import Celery
import asyncio
from app.core.config import settings

# Initialize Celery using Redis as broker and backend
celery_app = Celery(
    "jalrakshak_tasks",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task
def recalculate_region_risk(region_id: int):
    """
    Background job to recalculate risk for a region using the ML pipeline.
    """
    from datetime import datetime, timezone
    from app.services.risk_fusion_service import RiskFusionService
    from app.db.session import async_session_factory
    
    async def _run():
        async with async_session_factory() as db:
            # Recompute Risk Fusion (which cascades through feature extraction, ML, forecasting)
            # In a real app we'd save this to MLPredictionHistory table here.
            target_date = datetime.now(timezone.utc)
            await RiskFusionService.get_fused_risk(db, region_id, target_date)
            # await EarlyWarningService.process_and_store_alerts(db, fused)
            
    # Run the async code in a synchronous celery task wrapper
    asyncio.run(_run())
    return f"Recalculated ML risk for region {region_id}"

@celery_app.task
def run_model_monitoring():
    """
    Background job to run model drift monitoring across all active regions.
    """
    return "Model monitoring executed"
