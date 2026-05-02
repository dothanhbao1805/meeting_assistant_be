import asyncio
import httpx
from app.core.config import settings


async def fetch_participants(meeting_id: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=30) as client:
        # Bước 1: lấy meeting → participant_user_ids (là account_id)
        resp = await client.get(
            f"{settings.MEETING_SERVICE_URL}/internal/meetings/{meeting_id}",
        )
        resp.raise_for_status()
        meeting_data = resp.json()

        participant_user_ids = [
            p["user_id"]
            for p in meeting_data.get("participants", [])
            if p.get("user_id")
        ]

        if not participant_user_ids:
            return []

        # Bước 2: lấy full_name từ Company Service theo account_id
        async def fetch_one_member(account_id: str) -> dict | None:
            try:
                r = await client.get(
                    f"{settings.COMPANY_SERVICE_URL}/internal/members/by-account/{account_id}",
                )
                if r.status_code == 200:
                    data = r.json()
                    return {
                        "user_id": account_id,
                        "full_name": data.get("full_name", ""),
                        "email": data.get("email", ""),
                    }
            except Exception:
                pass
            return None

        results = await asyncio.gather(
            *[fetch_one_member(uid) for uid in participant_user_ids]
        )

    return [r for r in results if r is not None]