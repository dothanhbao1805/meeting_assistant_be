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
    "users": "http://auth-service:8001",
    "ai": "http://ai-service:8002",
    "meeting": "http://meeting-service:8005",
    "meetings": "http://meeting-service:8005",
    "company": "http://company-service:8003",
    "companies": "http://company-service:8003",
    "members": "http://company-service:8003",
    "transcription": "http://transcription-service:8004",
    "transcripts": "http://transcription-service:8004",
    "utterances": "http://transcription-service:8004",
    "analysis": "http://ai-analysis-service:8006",
}


@app.api_route(
    "/api/v1/{service}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
@app.api_route(
    "/api/v1/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def gateway(service: str, request: Request, path: str = ""):
    target_host = SERVICES.get(service)
    if not target_host:
        return Response(content=f"Service '{service}' not found", status_code=404)

    req_path = request.url.path
    if service == "analysis":
        req_path = req_path.replace("/api/v1/analysis", "/api/v1")
    url = f"{target_host}{req_path}"

    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            resp = await client.request(
                method=request.method,
                url=url,
                headers={
                    k: v for k, v in request.headers.items() if k.lower() != "host"
                },
                content=await request.body(),
                params=dict(request.query_params),
                timeout=60.0,
            )

            return Response(
                content=resp.content,
                status_code=resp.status_code,
                headers={
                    k: v
                    for k, v in resp.headers.items()
                    if k.lower() not in ["content-length", "content-encoding"]
                },
            )
        except Exception as e:
            return Response(content=f"Gateway error: {str(e)}", status_code=502)
