from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.config import settings
from app.db.session import get_db
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from contextlib import asynccontextmanager
from app.db.redis import redis_manager
from app.realtime.subscriber import EventSubscriber
from app.realtime.pubsub import pubsub_listener
from app.realtime.websocket import ws_manager
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ────────────────────────────────────────────────────────────
    logger.info("JalRakshak AI starting up...")

    # 1. Redis connection pool
    await redis_manager.connect()

    # 2. Redis Streams consumer (CEP / domain event processing)
    await EventSubscriber.start_background_consumer()

    # 3. Redis Pub/Sub listener (WebSocket broadcast delivery)
    await pubsub_listener.start()

    logger.info("JalRakshak AI startup complete.")
    yield

    # ── Shutdown ───────────────────────────────────────────────────────────
    logger.info("JalRakshak AI shutting down...")

    # Gracefully close all WebSocket clients
    await ws_manager.close_all()

    # Stop Pub/Sub listener
    await pubsub_listener.stop()

    # Release Redis connections
    await redis_manager.disconnect()

    logger.info("JalRakshak AI shutdown complete.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="JalRakshak AI - Public Health Decision Support System",
    lifespan=lifespan,
)

# CORS — update allow_origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/api/v1/health")
def health_check():
    return {"status": "ok", "message": "JalRakshak AI API is running"}


@app.get("/api/v1/health/database")
async def db_health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "message": "Database connection successful"}
    except Exception as e:
        return {"status": "error", "message": f"Database connection failed: {str(e)}"}
