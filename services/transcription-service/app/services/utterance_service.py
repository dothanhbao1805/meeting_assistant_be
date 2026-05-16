from sqlalchemy import UUID

from app.repositories.utterance_repo import UtteranceRepo
from app.schemas.utterance import (
    UtteranceResponse,
    UtteranceUpdateByUser,
    UtteranceUpdateResolved,
)
from typing import List
import logging
import uuid
from difflib import SequenceMatcher
from app.core.config import settings
import httpx

logger = logging.getLogger(__name__)


def _extract_word_corrections(old_text: str, new_text: str) -> list[dict]:
    old_words = old_text.lower().split()
    new_words = new_text.lower().split()
    corrections = []
    matcher = SequenceMatcher(None, old_words, new_words)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            wrong = " ".join(old_words[i1:i2])
            correct = " ".join(new_words[j1:j2])
            if wrong and correct:
                corrections.append({"wrong_text": wrong, "correct_text": correct})
    return corrections


async def _save_corrections_to_company(
    company_id: str,
    corrections: list[dict],
    context: str = None,  # thêm
):
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.post(
                f"{settings.COMPANY_SERVICE_URL}/internal/corrections",
                json={
                    "company_id": company_id,
                    "corrections": [{**c, "context": context} for c in corrections],
                },
            )
            resp.raise_for_status()
    except Exception as e:
        logger.warning(f"[utterance] Lưu corrections thất bại: {e}")


class UtteranceService:
    def __init__(self, utterance_repository: UtteranceRepo):
        self.utterance_repository = utterance_repository

    async def get_resolved_user_id_is_null(
        self, meeting_id: uuid.UUID
    ) -> List[UtteranceResponse]:
        return (
            await self.utterance_repository.get_resolved_user_id_is_null_by_meeting_id(
                meeting_id
            )
        )

    async def get_all_utterances_by_meeting_id(
        self, meeting_id: uuid.UUID
    ) -> List[UtteranceResponse]:
        return await self.utterance_repository.get_all_utterances_by_meeting_id(
            meeting_id
        )

    async def update_resolved_user_id_by_meeting_id_and_speaker_label(
        self, meeting_id: uuid.UUID, data: List[UtteranceUpdateResolved]
    ):
        return await self.utterance_repository.update_resolved_user_id_by_meeting_id_and_speaker_label(
            meeting_id, data
        )

    async def get_utterances_by_transcript_id(self, transcript_id: uuid.UUID) -> list:
        return await self.utterance_repository.get_by_transcript_id(transcript_id)

    async def update_resolved_user_id_by_utterance_ids(
        self, meeting_id: uuid.UUID, data: List[UtteranceUpdateByUser]
    ):
        return await self.utterance_repository.update_resolved_user_id_by_utterance_ids(
            meeting_id, data
        )

    async def update_utterance(self, utterance_id: UUID, payload) -> UtteranceResponse:
        from fastapi import HTTPException

        # 1. Lấy utterance hiện tại
        utterance = await self.utterance_repository.get_by_id(utterance_id)
        if not utterance:
            raise HTTPException(status_code=404, detail="Utterance không tồn tại")

        old_text = utterance.text

        # 2. Lưu original_text lần đầu edit
        update_data = {"text": payload.text, "is_edited": True}
        if not utterance.is_edited:
            update_data["original_text"] = old_text

        # 3. Update vào DB
        updated = await self.utterance_repository.update(utterance_id, update_data)
        await self.utterance_repository.db.commit()
        await self.utterance_repository.db.refresh(updated)

        # 4. Extract corrections và lưu vào company-service (non-blocking)
        if payload.text != old_text:
            corrections = _extract_word_corrections(old_text, payload.text)
            if corrections:
                company_id = (
                    await self.utterance_repository.get_company_id_by_utterance(
                        utterance_id
                    )
                )
                if company_id:
                    await _save_corrections_to_company(
                        company_id, corrections, context=old_text
                    )

        return UtteranceResponse.model_validate(updated)
