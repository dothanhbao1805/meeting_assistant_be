from fastapi import FastAPI
from app.routers import summarize

app = FastAPI(title="AI Service")

app.include_router(summarize.router)

@app.get("/health")
def health():
    return {"status": "ok"}
