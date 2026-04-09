import os
import tempfile
from openai import AsyncOpenAI
from app.core.config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

SUPPORTED_FORMATS = {".mp3", ".mp4", ".wav", ".m4a", ".webm", ".mpeg", ".mpga", ".ogg"}


async def transcribe_audio(file_bytes: bytes, filename: str) -> dict:
    ext = os.path.splitext(filename)[1].lower()

    if ext not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Định dạng '{ext}' không được hỗ trợ. Hỗ trợ: {SUPPORTED_FORMATS}"
        )

    # Ghi file tạm để truyền vào Whisper (API yêu cầu file object)
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as audio_file:
            response = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="vi",  # Tiếng Việt — bỏ dòng này nếu muốn auto-detect
                response_format="verbose_json",  # Trả về chi tiết: segments, duration,...
            )
    finally:
        os.unlink(tmp_path)  # Xóa file tạm dù có lỗi hay không

    return {
        "text": response.text,
        "language": response.language,
        "duration": response.duration,
        "segments": [
            {
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip(),
            }
            for seg in (response.segments or [])
        ],
    }
