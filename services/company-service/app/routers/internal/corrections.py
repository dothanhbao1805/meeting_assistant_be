from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_company_db
from app.repositories import correction_repo

router = APIRouter(prefix="/internal/corrections", tags=["internal"])


class CorrectionItem(BaseModel):
    wrong_text: str
    correct_text: str


class SaveCorrectionsRequest(BaseModel):
    company_id: UUID
    corrections: list[CorrectionItem]


class CorrectionResponse(BaseModel):
    id: UUID
    wrong_text: str
    correct_text: str
    frequency: int

    class Config:
        from_attributes = True


@router.post("", status_code=201)
async def save_corrections(
    body: SaveCorrectionsRequest,
    db: AsyncSession = Depends(get_company_db),
):
    """ai-analysis-service gọi để lưu corrections khi user sửa task"""
    saved = []
    for item in body.corrections:
        correction = await correction_repo.upsert_correction(
            db=db,
            company_id=body.company_id,
            wrong_text=item.wrong_text,
            correct_text=item.correct_text,
        )
        saved.append(correction)
    await db.commit()
    return {"saved": len(saved)}


@router.get("/{company_id}", response_model=list[CorrectionResponse])
async def get_corrections(
    company_id: UUID,
    db: AsyncSession = Depends(get_company_db),
):
    """transcription-service gọi để lấy corrections trước khi apply"""
    return await correction_repo.get_corrections_by_company(db, company_id)
