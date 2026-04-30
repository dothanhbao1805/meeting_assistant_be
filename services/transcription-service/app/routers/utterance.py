import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.utterance import Utterance

router = APIRouter(prefix="/utterances", tags=["Utterances"])


@router.get("/{transcript_id}")
async def get_utterances(
    transcript_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Utterance)
        .where(Utterance.transcript_id == transcript_id)
        .order_by(Utterance.sequence_order)
    )
    utterances = result.scalars().all()

    if not utterances:
        raise HTTPException(status_code=404, detail="Không tìm thấy utterances")

    return [
        {
            "id": str(u.id),
            "transcript_id": str(u.transcript_id),
            "speaker_label": u.speaker_label,
            "resolved_user_id": str(u.resolved_user_id) if u.resolved_user_id else None,
            "text": u.text,
            "start_time_ms": u.start_time_ms,
            "end_time_ms": u.end_time_ms,
            "confidence": u.confidence,
            "sequence_order": u.sequence_order,
        }
        for u in utterances
    ]
