from fastapi import FastAPI

from app.routers import meeting


app = FastAPI(title="Meeting Service")


app.include_router(meeting.router, prefix="/api/v1")
