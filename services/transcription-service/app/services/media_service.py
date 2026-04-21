import os
import requests
from dotenv import load_dotenv

load_dotenv()

MEETING_SERVICE_URL = os.getenv("MEETING_SERVICE_URL")


def get_media_file(media_file_id: str):
    if not MEETING_SERVICE_URL:
        raise Exception("Missing MEETING_SERVICE_URL")

    url = f"{MEETING_SERVICE_URL}/api/v1/meeting-files/{media_file_id}"

    # 🔥 debug tại đây
    print("👉 CALL URL:", url)

    res = requests.get(url, timeout=5)

    print("👉 STATUS:", res.status_code)
    print("👉 RESPONSE:", res.text)

    if res.status_code != 200:
        raise Exception(f"Cannot get media file: {res.text}")

    return res.json()