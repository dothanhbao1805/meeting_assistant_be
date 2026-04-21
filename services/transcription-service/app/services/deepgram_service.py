import requests
import os
from dotenv import load_dotenv

load_dotenv()

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")


def call_deepgram(url: str, options: dict):
    if not DEEPGRAM_API_KEY:
        raise Exception("Missing DEEPGRAM_API_KEY")

    res = requests.post(
        "https://api.deepgram.com/v1/listen",
        params=options,
        headers={
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": "application/json",
        },
        json={"url": url},
        timeout=120,
    )

    if res.status_code == 400:
        print(">>> DEEPGRAM ERROR DETAIL:", res.text)

    res.raise_for_status()

    data = res.json()
    print(">>> FULL RESPONSE:", data)

    return {
        "request_id": data.get("metadata", {}).get("request_id"),
        "transcript": (
            data.get("results", {})
            .get("channels", [{}])[0]
            .get("alternatives", [{}])[0]
            .get("transcript")
        ),
    }