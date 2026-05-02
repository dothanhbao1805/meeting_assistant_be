import asyncio
from fastapi import FastAPI

from fastapi.openapi.utils import get_openapi
from app.routers import job, webhook, transcript, utterance
from app.worker import run_worker

app = FastAPI(title="Transcription Service")

app.include_router(job.router, prefix="/api/v1")
app.include_router(webhook.router, prefix="/api/v1")

app.include_router(transcript.router)
app.include_router(utterance.router, prefix="/api/v1")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    schema.setdefault("components", {})["securitySchemes"] = {
        "HTTPBearer": {
            "type": "http",
            "scheme": "bearer",
        }
    }
    for path in schema["paths"].values():
        for method in path.values():
            method["security"] = [{"HTTPBearer": []}]
    app.openapi_schema = schema
    return schema

app.openapi = custom_openapi


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(run_worker())


@app.get("/")
def root():
    return {"service": "transcription-service", "status": "ok"}