# api-gateway/main.py
from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI()

# ─── CORS ──────────────────────────────────────────────────────────────────────
# Cho phép frontend React (localhost:3000 / 5173) gọi vào gateway
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://172.31.176.1:5173",
        "http://192.168.100.208:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Service registry ──────────────────────────────────────────────────────────
# Key = segment trong URL: /api/v1/{service}/...
SERVICES = {
    "auth": "http://auth-service:8001",
    "ai": "http://ai-service:8002",
    "company": "http://company-service:8003",
    "transcription": "http://transcription-service:8004",
    "meeting": "http://meeting-service:8005",
    "ai-analysis": "http://ai-analysis-service:8006",
    "integration": "http://integration-service:8007",
}


# ─── Proxy route ──────────────────────────────────────────────────────────────
# Frontend gọi:  POST /api/v1/auth/login
# Gateway forward: POST http://auth-service:8001/api/v1/login
#
# Quy tắc: /api/v1/{service}/{path} → {SERVICE_URL}/api/v1/{path}
@app.api_route(
    "/api/v1/{service}/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def gateway(service: str, path: str, request: Request):
    target_base = SERVICES.get(service)

    if not target_base:
        return Response(
            content=f'{{"detail": "Service \'{service}\' not found"}}',
            status_code=404,
            media_type="application/json",
        )

    url = f"{target_base}/api/v1/{service}/{path}"
    if request.url.query:
        url += f"?{request.url.query}"

    # Lọc header gửi đi
    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in ("host", "content-length")
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=await request.body(),
            )
        except httpx.ConnectError:
            return Response(
                content=f'{{"detail": "Cannot connect to service \'{service}\'"}}',
                status_code=503,
                media_type="application/json",
            )
        except httpx.TimeoutException:
            return Response(
                content=f'{{"detail": "Service \'{service}\' timed out"}}',
                status_code=504,
                media_type="application/json",
            )
        except Exception as e:
            # Bắt toàn bộ lỗi còn lại để gateway không bị crash
            return Response(
                content=f'{{"detail": "Gateway internal error: {str(e)}"}}',
                status_code=500,
                media_type="application/json",
            )

    # --- ĐIỂM QUAN TRỌNG: Lọc header trả về ---
    # Bỏ qua các header có thể làm Uvicorn/FastAPI bị crash
    excluded_headers = {
        "content-encoding",
        "content-length",
        "transfer-encoding",
        "connection",
    }
    response_headers = {
        k: v for k, v in resp.headers.items() if k.lower() not in excluded_headers
    }

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=response_headers,
        media_type=resp.headers.get("content-type", "application/json"),
    )


# ─── Health check ──────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "services": list(SERVICES.keys())}
