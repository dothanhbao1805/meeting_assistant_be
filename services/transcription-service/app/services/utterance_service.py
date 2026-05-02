from app.repositories.utterance_repo import UtteranceRepo
from app.schemas.utterance import UtteranceResponse, UtteranceUpdateResolved
from typing import List
import uuid


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
