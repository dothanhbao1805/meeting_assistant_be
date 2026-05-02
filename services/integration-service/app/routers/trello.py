import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.trello import TrelloSyncRequest, TrelloSyncResponse
from app.services.trello_service import sync_tasks_to_trello

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/trello", tags=["Trello"])


@router.post("/sync", response_model=TrelloSyncResponse)
async def sync_trello(
    payload: TrelloSyncRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger bởi event tasks.confirmed hoặc admin sync thủ công.
    """
    result = await sync_tasks_to_trello(
        db=db,
        meeting_id=str(payload.meeting_id),
        company_id=str(payload.company_id),
        trello_board_id=payload.trello_board_id,
        trello_list_id=payload.trello_list_id,
        confirmed_tasks=payload.confirmed_tasks,
    )
    return TrelloSyncResponse(**result)
