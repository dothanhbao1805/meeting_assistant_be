from fastapi import FastAPI
from app.routers.internal import members as internal_members
from app.routers import company, member, trello_boards
from app.routers.internal import corrections as internal_corrections


app = FastAPI(title="Company Service")

app.include_router(company.router, prefix="/api/v1")
app.include_router(member.router, prefix="/api/v1")
app.include_router(trello_boards.router, prefix="/api/v1")
app.include_router(internal_members.router, prefix="/api/v1")
app.include_router(internal_corrections.router, prefix="/api/v1")
