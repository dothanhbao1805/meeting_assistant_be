from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import uuid

from app.repositories import trello_boards_repo
from app.schemas.trello_boards import TrelloBoardCreate, TrelloBoardUpdate, TrelloBoardResponse
from app.services import trello_sync_service


async def get_trello_board_by_id(db: AsyncSession, board_id: uuid.UUID) -> TrelloBoardResponse:
    board = await trello_boards_repo.get_trello_board_by_id(db, board_id)
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trello board không tìm thấy",
        )
    return TrelloBoardResponse.model_validate(board)


async def get_trello_boards_by_company_id(db: AsyncSession, company_id: uuid.UUID) -> list[TrelloBoardResponse]:
    boards = await trello_boards_repo.get_trello_boards_by_company_id(db, company_id)
    return [TrelloBoardResponse.model_validate(board) for board in boards]


async def get_all_trello_boards(db: AsyncSession) -> list[TrelloBoardResponse]:
    boards = await trello_boards_repo.get_all_trello_boards(db)
    return [TrelloBoardResponse.model_validate(board) for board in boards]


async def create_trello_board(db: AsyncSession, data: TrelloBoardCreate) -> TrelloBoardResponse:
    # Check if board with same trello_board_id already exists
    existing_board = await trello_boards_repo.get_trello_board_by_trello_id(db, data.trello_board_id)
    if existing_board:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trello board này đã được thêm vào hệ thống",
        )
    
    board = await trello_boards_repo.create_trello_board(
        db,
        company_id=data.company_id,
        trello_board_id=data.trello_board_id,
        name=data.name,
        trello_url=data.trello_url,
    )
    return TrelloBoardResponse.model_validate(board)


async def update_trello_board(
    db: AsyncSession, board_id: uuid.UUID, data: TrelloBoardUpdate
) -> TrelloBoardResponse:
    board = await trello_boards_repo.update_trello_board(
        db,
        board_id=board_id,
        name=data.name,
        trello_url=data.trello_url,
        synced_at=data.synced_at,
    )
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trello board không tìm thấy",
        )
    return TrelloBoardResponse.model_validate(board)


async def delete_trello_board(db: AsyncSession, board_id: uuid.UUID) -> None:
    success = await trello_boards_repo.delete_trello_board(db, board_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trello board không tìm thấy",
        )


async def sync_trello_boards(
    db: AsyncSession, company_id: uuid.UUID, api_key: str, token: str
) -> dict:
    """
    Sync boards from Trello API and save to database
    
    Args:
        db: Database session
        company_id: Company ID
        api_key: Trello API key
        token: Trello token
    
    Returns:
        Dictionary with synced count and created boards
    """
    # Fetch boards from Trello
    boards = await trello_sync_service.fetch_trello_boards(api_key, token)
    
    created_boards = []
    skipped_count = 0
    now = datetime.utcnow()
    
    for board_data in boards:
        # Check if board already exists
        existing = await trello_boards_repo.get_trello_board_by_trello_id(db, board_data["id"])
        
        if existing:
            skipped_count += 1
            continue
        
        # Create new board
        board = await trello_boards_repo.create_trello_board(
            db=db,
            company_id=company_id,
            trello_board_id=board_data["id"],
            name=board_data["name"],
            trello_url=board_data.get("url"),
        )
        
        # Update synced_at
        board = await trello_boards_repo.update_trello_board(
            db=db,
            board_id=board.id,
            synced_at=now,
        )
        
        created_boards.append(TrelloBoardResponse.model_validate(board))
    
    return {
        "synced_count": len(created_boards),
        "created_boards": created_boards,
        "skipped_boards": skipped_count,
    }

