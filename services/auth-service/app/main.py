from fastapi import FastAPI

from app.routers import users
from app.routers import auth
from app.routers import internal


app = FastAPI(title="Auth Service")


app.include_router(users.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(internal.router)


@app.get("/health")
def health():
    return {"status": "ok"}