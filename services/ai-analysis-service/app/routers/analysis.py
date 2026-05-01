import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.repositories.analysis_repo import MeetingAnalysisRepo
from app.schemas.analysis import MeetingAnalysisResponse

router = APIRouter(prefix="/meetings", tags=["Meeting Analysis"])


@router.get("/{meeting_id}/analysis", response_model=MeetingAnalysisResponse)
async def get_meeting_analysis(
    meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    repo = MeetingAnalysisRepo(db)

    job = await repo.get_latest_job_with_results(meeting_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Chưa có analysis job nào cho meeting {meeting_id}",
        )

    # Nếu job chưa done, trả về status hiện tại, không có data
    if job.status != "done":
        return MeetingAnalysisResponse(status=job.status)

    unresolved_speakers = await repo.get_unresolved_speakers(meeting_id)

    return MeetingAnalysisResponse(
        status=job.status,
        summary=job.summary,
        tasks=job.tasks,
        unresolved_speakers=unresolved_speakers if unresolved_speakers else None,
    )
