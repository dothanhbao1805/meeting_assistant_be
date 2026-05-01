# seed.py — chạy từ thư mục transcription-service
import asyncio
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import TranscriptionJob, Transcript, Utterance

DATABASE_URL = "postgresql+asyncpg://trans_user:trans_pass@db_transcription:5432/transcription_db"

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def seed():
    async with AsyncSessionLocal() as db:
        meeting_id   = uuid.uuid4()
        media_file_id = uuid.uuid4()

        # ── Job ──────────────────────────────────────────────
        job = TranscriptionJob(
            id=uuid.uuid4(),
            meeting_id=meeting_id,
            media_file_id=media_file_id,
            status="done",
            model="nova-2",
            processing_ms=4200,
            started_at=datetime(2026, 4, 19, 10, 0, 0, tzinfo=timezone.utc),
            completed_at=datetime(2026, 4, 19, 10, 0, 4, tzinfo=timezone.utc),
        )
        db.add(job)
        await db.flush()

        # ── Transcript ───────────────────────────────────────
        transcript = Transcript(
            id=uuid.uuid4(),
            job_id=job.id,
            meeting_id=meeting_id,
            full_text="Chào mọi người. Hôm nay chúng ta họp về sprint 3. Tôi nghĩ deadline cần lùi lại.",
            edited_text=None,
            is_edited=False,
            speaker_count=2,
            confidence_avg=0.91,
            language_detected="vi",
            created_at=datetime(2026, 4, 19, 10, 0, 4, tzinfo=timezone.utc),
        )
        db.add(transcript)
        await db.flush()

        # ── Utterances ───────────────────────────────────────
        utterances = [
            Utterance(
                id=uuid.uuid4(),
                transcript_id=transcript.id,
                speaker_label="Speaker_0",
                text="Chào mọi người.",
                start_time_ms=0,
                end_time_ms=1500,
                confidence=0.95,
                sequence_order=1,
            ),
            Utterance(
                id=uuid.uuid4(),
                transcript_id=transcript.id,
                speaker_label="Speaker_0",
                text="Hôm nay chúng ta họp về sprint 3.",
                start_time_ms=1600,
                end_time_ms=4000,
                confidence=0.93,
                sequence_order=2,
            ),
            Utterance(
                id=uuid.uuid4(),
                transcript_id=transcript.id,
                speaker_label="Speaker_1",
                text="Tôi nghĩ deadline cần lùi lại.",
                start_time_ms=4200,
                end_time_ms=6500,
                confidence=0.88,
                sequence_order=3,
            ),
        ]
        db.add_all(utterances)
        await db.commit()

        print(f"✅ Done!")
        print(f"   meeting_id  : {meeting_id}")
        print(f"   job_id      : {job.id}")
        print(f"   transcript_id: {transcript.id}")

asyncio.run(seed())