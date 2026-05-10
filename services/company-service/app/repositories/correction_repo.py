import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.vocabulary import TranscriptionCorrection


async def upsert_correction(
    db: AsyncSession,
    company_id: uuid.UUID,
    wrong_text: str,
    correct_text: str,
) -> TranscriptionCorrection:
    # Kiểm tra đã tồn tại chưa
    result = await db.execute(
        select(TranscriptionCorrection).where(
            TranscriptionCorrection.company_id == company_id,
            TranscriptionCorrection.wrong_text == wrong_text.lower(),
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Cập nhật correct_text mới nhất và tăng frequency
        existing.correct_text = correct_text.lower()
        existing.frequency += 1
        await db.flush()
        return existing

    # Tạo mới
    correction = TranscriptionCorrection(
        company_id=company_id,
        wrong_text=wrong_text.lower(),
        correct_text=correct_text.lower(),
        frequency=1,
    )
    db.add(correction)
    await db.flush()
    return correction


async def get_corrections_by_company(
    db: AsyncSession,
    company_id: uuid.UUID,
) -> list[TranscriptionCorrection]:
    result = await db.execute(
        select(TranscriptionCorrection)
        .where(TranscriptionCorrection.company_id == company_id)
        .order_by(TranscriptionCorrection.frequency.desc())
    )
    return result.scalars().all()
