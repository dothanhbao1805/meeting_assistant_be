from fastapi import APIRouter
from app.services.groq_service import summarize_text
from app.schemas.summarize import SummarizeRequest, SummarizeResponse

router = APIRouter(prefix="/api/v1/ai", tags=["AI"])

@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(req: SummarizeRequest):
    result = await summarize_text(req.text)
    return result