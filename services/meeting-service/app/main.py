from fastapi import FastAPI

from app.routers import meeting
from app.routers import meeting_file

app = FastAPI(title="Meeting Service")


app.include_router(meeting.router, prefix="/api/v1")
app.include_router(meeting_file.router, prefix="/api/v1")
