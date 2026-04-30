from fastapi import FastAPI
from app.routers import speaker
from app.routers import task

app = FastAPI(title="AI Analysis Service")

app.include_router(router=speaker.router)
app.include_router(router=task.router, prefix="/api/v1")
def root():
    return {"service": "ai-analysis-service", "status": "ok"}
