from fastapi import FastAPI

app = FastAPI(title="AI Analysis Service")


@app.get("/")
def root():
    return {"service": "ai-analysis-service", "status": "ok"}
