import hashlib
import uuid
import asyncio
import tempfile
import os

from ffmpeg import FFmpeg
from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from storage3 import create_client as create_storage_client

from app.core.config import settings
from app.models import Meeting, MeetingFile, MeetingParticipant
from app.repositories.meeting_repository import MeetingRepository
from app.schemas.meeting import MeetingCreate

MAX_UPLOAD_BYTES = 45 * 1024 * 1024

SUPPORTED_VIDEO_TYPES = {"mp4", "mov", "avi", "mkv", "webm"}
SUPPORTED_AUDIO_TYPES = {"mp3", "wav", "m4a", "ogg"}


class MeetingService:
    def __init__(self, db: AsyncSession):
        self.repo = MeetingRepository(db)
        self.db = db
        self.storage = create_storage_client(
            f"{settings.SUPABASE_URL}/storage/v1/",
            {
                "apikey": settings.SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
            },
            is_async=False,
        )

    def _convert_to_mp3(self, input_path: str, output_path: str) -> None:
        ffmpeg = (
            FFmpeg()
            .input(input_path)
            .output(
                output_path,
                {"b:a": "64k"},
                ac=1,
                ar=16000,
                f="mp3",
            )
        )
        ffmpeg.execute()

    async def _process_file(self, file: UploadFile) -> tuple[bytes, str]:
        content = await file.read()
        file_ext = file.filename.rsplit(".", 1)[-1].lower()

        if file_ext in SUPPORTED_VIDEO_TYPES:
            with tempfile.TemporaryDirectory() as tmp_dir:
                input_path = os.path.join(tmp_dir, f"input.{file_ext}")
                output_path = os.path.join(tmp_dir, "output.mp3")

                with open(input_path, "wb") as f:
                    f.write(content)

                await asyncio.get_event_loop().run_in_executor(
                    None, self._convert_to_mp3, input_path, output_path
                )

                with open(output_path, "rb") as f:
                    content = f.read()

            file_ext = "mp3"

        elif file_ext not in SUPPORTED_AUDIO_TYPES:
            raise HTTPException(
                status_code=415,
                detail=f"Định dạng '{file_ext}' không được hỗ trợ.",
            )

        if len(content) > MAX_UPLOAD_BYTES:
            size_mb = len(content) / 1024 / 1024
            raise HTTPException(
                status_code=413,
                detail=f"File sau khi xử lý vẫn quá lớn ({size_mb:.1f}MB). Giới hạn là {MAX_UPLOAD_BYTES // 1024 // 1024}MB.",
            )

        return content, file_ext

    async def create_meeting_with_file(
        self,
        data: MeetingCreate,
        file: UploadFile,
        current_user_id: uuid.UUID,
    ) -> Meeting:
        content, file_ext = await self._process_file(file)

        checksum = hashlib.sha256(content).hexdigest()
        storage_path = f"{current_user_id}/{uuid.uuid4()}.{file_ext}"

        try:
            self.storage.from_(settings.SUPABASE_BUCKET).upload(
                path=storage_path,
                file=content,
                file_options={"content-type": f"audio/{file_ext}"},
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload thất bại: {e}")

        public_url = self.storage.from_(settings.SUPABASE_BUCKET).get_public_url(
            storage_path
        )

        meeting = await self.repo.create(
            Meeting(
                company_id=data.company_id,
                created_by_user_id=current_user_id,
                title=data.title,
                status="uploaded",
                scheduled_at=data.scheduled_at,
                language_code=data.language_code or "vi",
            )
        )

        for user_id in set([*(data.participant_user_ids or []), current_user_id]):
            await self.repo.add_participant(
                MeetingParticipant(meeting_id=meeting.id, user_id=user_id)
            )

        await self.repo.add_file(
            MeetingFile(
                meeting_id=meeting.id,
                storage_path=public_url,
                storage_bucket=settings.SUPABASE_BUCKET,
                file_type=file_ext,
                file_size_bytes=len(content),
                checksum_sha256=checksum,
            )
        )

        await self.db.commit()

        created_meeting = await self.repo.get_by_id(meeting.id)
        if not created_meeting:
            raise HTTPException(status_code=500, detail="Không tải lại được meeting sau khi tạo")

        return created_meeting

    async def get_meeting(self, meeting_id: uuid.UUID) -> Meeting:
        meeting = await self.repo.get_by_id(meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting không tồn tại")
        return meeting

    async def get_meetings_by_company(self, company_id: uuid.UUID) -> list[Meeting]:
        return await self.repo.get_by_company(company_id)