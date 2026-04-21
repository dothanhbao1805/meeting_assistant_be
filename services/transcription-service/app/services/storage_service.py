# app/services/storage_service.py

import os
import requests
from urllib.parse import urlparse
from app.services.media_service import get_media_file
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

EXPIRES_IN = 3600


def extract_object_path(full_url: str, bucket: str) -> str:
    parsed = urlparse(full_url)

    # tách sau bucket
    parts = parsed.path.split(f"/{bucket}/")

    if len(parts) != 2:
        raise Exception(f"Invalid storage_path: {full_url}")

    return parts[1]  # ví dụ: abc/xyz.mp3


def get_signed_url(media_file_id: str) -> str:
    media = get_media_file(media_file_id)

    bucket = media["storage_bucket"]
    raw_path = media["storage_path"]

    # 🔥 fix ở đây
    object_path = extract_object_path(raw_path, bucket)

    endpoint = f"{SUPABASE_URL}/storage/v1/object/sign/{bucket}/{object_path}"

    res = requests.post(
        endpoint,
        json={"expiresIn": EXPIRES_IN},
        headers={
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "apikey": SUPABASE_SERVICE_KEY,
            "Content-Type": "application/json",
        },
        timeout=10,
    )

    if res.status_code != 200:
        raise Exception(f"Supabase error: {res.text}")

    data = res.json()
    signed_path = data.get("signedURL") or data.get("signedUrl")

    if not signed_path:
        raise Exception(f"No signed URL: {data}")

    return f"{SUPABASE_URL}/storage/v1{signed_path}"