import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.utterance import Utterance
from app.models.transcript import Transcript
from sqlalchemy import update, exists
from typing import List
from app.models.transcription_job import TranscriptionJob


class UtteranceRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> Utterance:
        """Tạo utterance mới"""
        utterance = Utterance(
            transcript_id=uuid.UUID(data["transcript_id"]),
            speaker_label=data.get("speaker_label"),
            resolved_user_id=data.get("resolved_user_id"),
            text=data.get("text", ""),
            start_time_ms=data.get("start_time_ms"),
            end_time_ms=data.get("end_time_ms"),
            confidence=data.get("confidence"),
            sequence_order=data.get("sequence_order"),
        )
        self.db.add(utterance)
        await self.db.flush()
        return utterance

    async def create_batch(self, utterances_data: list[dict]) -> list[Utterance]:
        """Tạo nhiều utterance cùng lúc"""
        utterances = []
        for data in utterances_data:
            utterance = Utterance(
                transcript_id=uuid.UUID(data["transcript_id"]),
                speaker_label=data.get("speaker_label"),
                resolved_user_id=data.get("resolved_user_id"),
                text=data.get("text", ""),
                start_time_ms=data.get("start_time_ms"),
                end_time_ms=data.get("end_time_ms"),
                confidence=data.get("confidence"),
                sequence_order=data.get("sequence_order"),
            )
            self.db.add(utterance)
            utterances.append(utterance)

        await self.db.flush()
        return utterances

    async def get_by_id(self, utterance_id: uuid.UUID) -> Utterance | None:
        """Lấy utterance theo ID"""
        result = await self.db.execute(
            select(Utterance).where(Utterance.id == utterance_id)
        )
        return result.scalar_one_or_none()

    async def get_by_transcript_id(self, transcript_id: uuid.UUID) -> list[Utterance]:
        """Lấy tất cả utterance của transcript, sắp xếp theo sequence"""
        result = await self.db.execute(
            select(Utterance)
            .where(Utterance.transcript_id == transcript_id)
            .order_by(Utterance.sequence_order)
        )
        return list(result.scalars().all())

    async def get_by_speaker_label(
        self, transcript_id: uuid.UUID, speaker_label: str
    ) -> list[Utterance]:
        """Lấy tất cả utterance của speaker cụ thể"""
        result = await self.db.execute(
            select(Utterance)
            .where(
                Utterance.transcript_id == transcript_id,
                Utterance.speaker_label == speaker_label,
            )
            .order_by(Utterance.sequence_order)
        )
        return list(result.scalars().all())

    async def update(
        self,
        utterance_id: uuid.UUID,
        data: dict,
    ) -> Utterance | None:
        """Cập nhật utterance"""
        utterance = await self.get_by_id(utterance_id)
        if not utterance:
            return None

        for key, value in data.items():
            if hasattr(utterance, key):
                setattr(utterance, key, value)

        await self.db.flush()
        return utterance

    async def update_batch(
        self,
        utterance_ids: list[uuid.UUID],
        data: dict,
    ) -> int:
        """Cập nhật nhiều utterance, trả về số record được cập nhật"""
        result = await self.db.execute(
            select(Utterance).where(Utterance.id.in_(utterance_ids))
        )
        utterances = result.scalars().all()

        for utterance in utterances:
            for key, value in data.items():
                if hasattr(utterance, key):
                    setattr(utterance, key, value)

        await self.db.flush()
        return len(utterances)

    async def get_resolved_user_id_is_null_by_meeting_id(
        self,
        meeting_id: uuid.UUID,
    ) -> list[Utterance]:
        stmt = (
            select(Utterance)
            .join_from(Utterance, Transcript, Utterance.transcript_id == Transcript.id)
            .where(
                Transcript.meeting_id == meeting_id,
                Utterance.resolved_user_id.is_(None),
            )
            .order_by(Utterance.sequence_order)
        )
        result = await self.db.execute(stmt)

        return list(result.scalars().all())

    async def get_all_utterances_by_meeting_id(
        self,
        meeting_id: uuid.UUID,
    ) -> list[Utterance]:
        stmt = (
            select(Utterance)
            .join(Utterance.transcript)
            .where(Transcript.meeting_id == meeting_id)
            .order_by(Utterance.sequence_order)
        )

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update_resolved_user_id_by_meeting_id_and_speaker_label(
        self, meeting_id: uuid.UUID, data: List
    ) -> dict:

        subquery = (
            select(Transcript.id)
            .where(Transcript.meeting_id == meeting_id)
            .scalar_subquery()
        )

        updated_speakers = 0

        for item in data:
            stmt = (
                update(Utterance)
                .where(Utterance.speaker_label == item.speaker_label)
                .where(Utterance.transcript_id.in_(subquery))
                .where(Utterance.resolved_user_id.is_(None))
                .values(resolved_user_id=item.resolved_user_id)
            )

            result = await self.db.execute(stmt)

            if (result.rowcount or 0) > 0:
                updated_speakers += 1

            await self.db.commit()

        exists_stmt = select(
            exists().where(
                Utterance.transcript_id.in_(subquery),
                Utterance.resolved_user_id.is_(None),
            )
        )

        result = await self.db.execute(exists_stmt)
        has_unresolved = result.scalar()

        return {"updated_count": updated_speakers, "all_resolved": not has_unresolved}

    async def update_resolved_user_id_by_utterance_ids(
        self,
        meeting_id: uuid.UUID,
        data: List,
    ) -> dict:
        subquery = (
            select(Transcript.id)
            .where(Transcript.meeting_id == meeting_id)
            .scalar_subquery()
        )

        updated_count = 0

        for item in data:
            stmt = (
                update(Utterance)
                .where(Utterance.id == item.id)
                .where(
                    Utterance.transcript_id.in_(subquery)
                )  # đảm bảo utterance thuộc meeting này
                .values(resolved_user_id=item.resolved_user_id)
            )
            result = await self.db.execute(stmt)
            if (result.rowcount or 0) > 0:
                updated_count += 1

        await self.db.commit()

        exists_stmt = select(
            exists().where(
                Utterance.transcript_id.in_(subquery),
                Utterance.resolved_user_id.is_(None),
            )
        )
        result = await self.db.execute(exists_stmt)
        has_unresolved = result.scalar()

        return {
            "updated_count": updated_count,
            "all_resolved": not has_unresolved,
        }

    async def get_company_id_by_utterance(self, utterance_id: uuid.UUID) -> str | None:
        result = await self.db.execute(
            select(TranscriptionJob.company_id)
            .join(Transcript, Transcript.job_id == TranscriptionJob.id)
            .join(Utterance, Utterance.transcript_id == Transcript.id)
            .where(Utterance.id == utterance_id)
        )
        company_id = result.scalar_one_or_none()
        return str(company_id) if company_id else None
