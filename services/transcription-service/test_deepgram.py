from app.services.storage_service import get_signed_url
from app.services.deepgram_service import call_deepgram

MEDIA_FILE_ID = "d1d3d777-a7ca-419e-828b-2bc95aa444a2"  # cùng file bước 1

# Bước 1: lấy signed URL
print("Đang lấy signed URL...")
url = get_signed_url(MEDIA_FILE_ID)
print("✓ Signed URL:", url)

# Bước 2: gửi Deepgram
print("\nĐang gửi Deepgram, chờ xử lý...")
result = call_deepgram(url, {
    "model": "nova-2",
    "language": "vi",
    "diarize": "true",
    "punctuate": "true",
    "smart_format": "true",
})

print("request_id :", result["request_id"])
print("transcript  :", result["transcript"])