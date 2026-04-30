import asyncio
from fastapi import FastAPI
from app.routers import job, webhook, utterance
from app.worker import run_worker
from app.routers import transcript
from app.routers import utterance

app = FastAPI(title="Transcription Service")

app.include_router(job.router, prefix="/api/v1")
app.include_router(webhook.router, prefix="/api/v1")

app.include_router(transcript.router, prefix="/api/v1")
app.include_router(utterance.router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(run_worker())


@app.get("/")
def root():
    return {"service": "transcription-service", "status": "ok"}
