import asyncio
import logging


from fastapi import FastAPI
from app.routers import job
from app.routers.analysis import router as analysis_router
from app.routers.health import router as health_router
from app.worker import run_worker
from app.subscribers.transcription_subscriber import start_subscriber
from app.routers import speaker
from app.routers import task

app = FastAPI(title="AI Analysis Service")
app.include_router(job.router, prefix="/api/v1")
app.include_router(analysis_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_subscriber())
    asyncio.create_task(run_worker())


app.include_router(router=speaker.router)
app.include_router(router=task.router, prefix="/api/v1")


def root():
    return {"service": "ai-analysis-service", "status": "ok"}