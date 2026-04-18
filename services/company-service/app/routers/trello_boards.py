import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_company_db
from app.schemas.trello_boards import (
    TrelloBoardCreate,
    TrelloBoardUpdate,
    TrelloBoardResponse,
    TrelloSyncRequest,
    TrelloSyncResponse,
)
from app.services import trello_boards_service

router = APIRouter(prefix="/trello-boards", tags=["trello-boards"])


@router.get("", response_model=list[TrelloBoardResponse])
async def get_all_trello_boards(db: AsyncSession = Depends(get_company_db)):
    """Get all trello boards"""
    return await trello_boards_service.get_all_trello_boards(db)


@router.get("/company/{company_id}", response_model=list[TrelloBoardResponse])
async def get_company_trello_boards(company_id: uuid.UUID, db: AsyncSession = Depends(get_company_db)):
    """Get all trello boards for a specific company"""
    return await trello_boards_service.get_trello_boards_by_company_id(db, company_id)


@router.get("/{board_id}", response_model=TrelloBoardResponse)
async def get_trello_board(board_id: uuid.UUID, db: AsyncSession = Depends(get_company_db)):
    """Get a specific trello board by ID"""
    return await trello_boards_service.get_trello_board_by_id(db, board_id)


@router.post("", response_model=TrelloBoardResponse, status_code=status.HTTP_201_CREATED)
async def create_trello_board(data: TrelloBoardCreate, db: AsyncSession = Depends(get_company_db)):
    """Create a new trello board"""
    return await trello_boards_service.create_trello_board(db, data)


@router.post("/sync", response_model=TrelloSyncResponse, status_code=status.HTTP_200_OK)
async def sync_trello_boards(
    data: TrelloSyncRequest,
    db: AsyncSession = Depends(get_company_db),
):
    """
    Sync boards from Trello API using API key and token.
    
    Requires:
    - company_id: The company ID to associate boards with
    - trello_api_key: Your Trello API key (get from https://trello.com/app-key)
    - trello_token: Your Trello token (generate from API key page)
    """
    result = await trello_boards_service.sync_trello_boards(
        db=db,
        company_id=data.company_id,
        api_key=data.trello_api_key,
        token=data.trello_token,
    )
    return TrelloSyncResponse(
        synced_count=result["synced_count"],
        created_boards=result["created_boards"],
        skipped_boards=result["skipped_boards"],
    )


@router.put("/{board_id}", response_model=TrelloBoardResponse)
async def update_trello_board(
    board_id: uuid.UUID, data: TrelloBoardUpdate, db: AsyncSession = Depends(get_company_db)
):
    """Update a trello board"""
    return await trello_boards_service.update_trello_board(db, board_id, data)


@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trello_board(board_id: uuid.UUID, db: AsyncSession = Depends(get_company_db)):
    """Delete a trello board"""
    await trello_boards_service.delete_trello_board(db, board_id)
