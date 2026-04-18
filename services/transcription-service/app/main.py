from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(title="Transcription Service")


@app.get("/")
def root():
    return {"service": "transcription-service", "status": "ok"}
