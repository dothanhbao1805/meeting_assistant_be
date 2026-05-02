from fastapi import FastAPI
from app.routers import company, member, trello_boards,internal

app = FastAPI(title="Company Service")

app.include_router(company.router,prefix="/api/v1")
app.include_router(member.router,prefix="/api/v1")
app.include_router(trello_boards.router,prefix="/api/v1")
app.include_router(internal.router)