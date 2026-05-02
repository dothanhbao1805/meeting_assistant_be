import httpx
from app.core.config import settings


async def fetch_utterances(transcript_id: str) -> list[dict]:
    url = f"{settings.TRANSCRIPTION_SERVICE_URL}/api/v1/utterances/transcript/{transcript_id}"

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()

    # Router utterance trả về list trực tiếp, không phải pagination
    if isinstance(data, list):
        return data

    # Nếu là pagination format thì lấy items
    return data.get("items", [])