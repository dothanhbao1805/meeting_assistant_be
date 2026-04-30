from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func

from app.db.database import get_db
from app.core.config import settings
from app.models.analysis_job import AnalysisJob
from groq import AsyncGroq

router = APIRouter(prefix="/health", tags=["Health"])


async def _check_db(db: AsyncSession) -> str:
    try:
        await db.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        return "error"


async def _check_groq() -> str:
    try:
        client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        await client.models.list()
        return "ok"
    except Exception:
        return "error"


async def _avg_processing_time(db: AsyncSession) -> int | None:
    """Trung bình thời gian xử lý của 50 jobs done gần nhất (ms)."""
    try:
        result = await db.execute(
            select(
                func.avg(
                    func.extract(
                        "epoch",
                        AnalysisJob.completed_at - AnalysisJob.created_at,
                    )
                    * 1000
                )
            )
            .where(AnalysisJob.status == "done")
            .order_by(AnalysisJob.created_at.desc())
            .limit(50)
        )
        avg = result.scalar()
        return int(avg) if avg is not None else None
    except Exception:
        return None


@router.get("/")
async def health_check(db: AsyncSession = Depends(get_db)):
    db_status, groq_status, avg_ms = (
        await _check_db(db),
        await _check_groq(),
        await _avg_processing_time(db),
    )

    return {
        "db": db_status,
        "groq_api": groq_status,
        "avg_processing_time_ms": avg_ms,
    }
