from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.sync import SyncQueueResponse, SyncStatusResponse
from app.services.sync_service import get_sync_queue as get_sync_queue_service
from app.services.sync_service import get_sync_status as get_sync_status_service

router = APIRouter(tags=["Sync"])


@router.get("/sync-queue", response_model=SyncQueueResponse)
async def get_sync_queue(
    meeting_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    job_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await get_sync_queue_service(
        db=db,
        meeting_id=meeting_id,
        status=status,
        job_type=job_type,
        limit=limit,
        offset=offset,
    )


@router.get("/sync-status/{meeting_id}", response_model=SyncStatusResponse)
async def get_sync_status(
    meeting_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    return await get_sync_status_service(db=db, meeting_id=meeting_id)
