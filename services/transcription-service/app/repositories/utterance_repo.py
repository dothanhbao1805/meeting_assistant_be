import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.utterance import Utterance


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

    async def get_by_transcript_id(
        self, transcript_id: uuid.UUID
    ) -> list[Utterance]:
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
