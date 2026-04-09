from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.AIServices.whisper_service import transcribe_audio

router = APIRouter(prefix="/upload", tags=["Upload"])

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB — giới hạn của Whisper API


@router.post("/test-whisper")
async def test_whisper(file: UploadFile = File(...)):
    """
    Endpoint thử nghiệm: upload file audio/video → gọi Whisper → trả về transcript.
    Chưa lưu vào DB, chỉ để kiểm tra Whisper API hoạt động đúng không.
    """
    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, detail="File vượt quá 25MB — giới hạn của Whisper API"
        )

    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="File rỗng")

    try:
        result = await transcribe_audio(file_bytes, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Whisper API lỗi: {str(e)}")

    return {
        "filename": file.filename,
        "file_size_kb": round(len(file_bytes) / 1024, 2),
        "transcript": result,
    }
