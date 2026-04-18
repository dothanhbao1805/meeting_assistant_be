import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.trello_boards import TrelloBoard


async def get_trello_board_by_id(db: AsyncSession, board_id: uuid.UUID) -> TrelloBoard | None:
    result = await db.execute(select(TrelloBoard).where(TrelloBoard.id == board_id))
    return result.scalar_one_or_none()


async def get_trello_board_by_trello_id(db: AsyncSession, trello_board_id: str) -> TrelloBoard | None:
    result = await db.execute(select(TrelloBoard).where(TrelloBoard.trello_board_id == trello_board_id))
    return result.scalar_one_or_none()


async def get_trello_boards_by_company_id(db: AsyncSession, company_id: uuid.UUID) -> list[TrelloBoard]:
    result = await db.execute(select(TrelloBoard).where(TrelloBoard.company_id == company_id))
    return result.scalars().all()


async def get_all_trello_boards(db: AsyncSession) -> list[TrelloBoard]:
    result = await db.execute(select(TrelloBoard))
    return result.scalars().all()


async def create_trello_board(
    db: AsyncSession,
    company_id: uuid.UUID,
    trello_board_id: str,
    name: str,
    trello_url: str | None = None,
) -> TrelloBoard:
    board = TrelloBoard(
        company_id=company_id,
        trello_board_id=trello_board_id,
        name=name,
        trello_url=trello_url,
    )
    db.add(board)
    await db.commit()
    await db.refresh(board)
    return board


async def update_trello_board(
    db: AsyncSession,
    board_id: uuid.UUID,
    name: str | None = None,
    trello_url: str | None = None,
    synced_at = None,
) -> TrelloBoard | None:
    board = await get_trello_board_by_id(db, board_id)
    if not board:
        return None
    
    if name is not None:
        board.name = name
    if trello_url is not None:
        board.trello_url = trello_url
    if synced_at is not None:
        board.synced_at = synced_at
    
    await db.commit()
    await db.refresh(board)
    return board


async def delete_trello_board(db: AsyncSession, board_id: uuid.UUID) -> bool:
    board = await get_trello_board_by_id(db, board_id)
    if board:
        await db.delete(board)
        await db.commit()
        return True
    return False
