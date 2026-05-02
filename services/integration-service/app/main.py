import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers import trello
from app.workers.integration_worker import run_worker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi động worker lắng nghe tasks.confirmed
    worker_task = asyncio.create_task(run_worker())
    logger.info("[MAIN] Integration Worker started")
    yield
    # Shutdown
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        logger.info("[MAIN] Integration Worker stopped")


app = FastAPI(
    title="Integration Service",
    description="Sync tasks to Trello, Google Calendar",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(trello.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"service": "integration-service", "status": "running"}
