from fastapi import FastAPI, Request, Response
import httpx
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

SERVICES = {
    "auth": "http://auth-service:8001",
    "ai": "http://ai-service:8002",
    "meeting": "http://meeting-service:8005",
    "company": "http://company-service:8003",
    "transcription": "http://transcription-service:8004",
}


@app.api_route("/api/v1/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def gateway(service: str, path: str, request: Request):
    target_host = SERVICES.get(service)
    if not target_host:
        return Response(content=f"Service '{service}' not found", status_code=404)

    url = f"{target_host}/api/v1/{service}/{path}"
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.request(
                method=request.method,
                url=url,
                headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
                content=await request.body(),
                params=dict(request.query_params),
                timeout=60.0
            )
            
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                headers={k: v for k, v in resp.headers.items() if k.lower() not in ["content-length", "content-encoding"]}
            )
        except Exception as e:
            return Response(content=f"Gateway error: {str(e)}", status_code=502)
