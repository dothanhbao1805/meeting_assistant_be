import httpx
from app.core.config import settings


async def fetch_utterances(transcript_id: str) -> list[dict]:
    url = f"{settings.TRANSCRIPTION_SERVICE_URL}/api/v1/transcripts/{transcript_id}/utterances"

    all_items = []
    page = 1
    limit = 50

    async with httpx.AsyncClient(timeout=30) as client:
        while True:
            response = await client.get(url, params={"page": page, "limit": limit})
            response.raise_for_status()
            data = response.json()

            items = data.get("items", [])
            all_items.extend(items)

            if not data.get("has_next"):
                break

            page += 1

    return all_items
