from fastapi import FastAPI

from app.routers.WebRouters import users
from app.routers.WebRouters import auth
from app.routers.AIRouters import upload

app = FastAPI(title="My App", version="0.1.0")
app.include_router(users.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(upload.router)


@app.get("/health")
def health():
    return {"status": "ok"}
