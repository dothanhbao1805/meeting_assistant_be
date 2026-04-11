# api-gateway/main.py
from fastapi import FastAPI, Request
import httpx

app = FastAPI()

SERVICES = {"auth": "http://auth-service:8001", "ai": "http://ai-service:8002"}


@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def gateway(service: str, path: str, request: Request):
    target = SERVICES.get(service)
    async with httpx.AsyncClient() as client:
        resp = await client.request(
            method=request.method,
            url=f"{target}/{path}",
            headers=dict(request.headers),
            content=await request.body(),
        )
    return httpx.Response(content=resp.content, status_code=resp.status_code)
