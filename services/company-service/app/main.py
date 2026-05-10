from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import company, member, trello_boards,internal

app = FastAPI(title="Company Service")
# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(company.router,prefix="/api/v1")
app.include_router(member.router,prefix="/api/v1")
app.include_router(trello_boards.router,prefix="/api/v1")
app.include_router(internal.router)