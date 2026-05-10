import asyncio
import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


async def fetch_participants(meeting_id: str, transcript_id: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=30) as client:
        # Bước 1: lấy meeting → participant_user_ids
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

        # Bước 2: lấy utterances để build speaker_label → user_id map
        speaker_to_user: dict[str, str] = {}
        try:
            utt_resp = await client.get(
                f"{settings.TRANSCRIPTION_SERVICE_URL}/api/v1/utterances/transcript/{transcript_id}",
            )
            if utt_resp.status_code == 200:
                for u in utt_resp.json():
                    label = u.get("speaker_label")
                    resolved = u.get("resolved_user_id")
                    if label and resolved and label not in speaker_to_user:
                        speaker_to_user[label] = resolved
        except Exception as e:
            logger.warning(f"fetch utterances failed: {e}")

        # user_id → speaker_label (reverse map)
        user_to_speaker = {v: k for k, v in speaker_to_user.items()}
        logger.info(f"speaker_to_user: {speaker_to_user}")
        logger.info(f"user_to_speaker: {user_to_speaker}")

        # Bước 3: lấy full_name từ Company Service
        async def fetch_one_member(account_id: str) -> dict | None:
            try:
                r = await client.get(
                    f"{settings.COMPANY_SERVICE_URL}/internal/members/{account_id}",  # ← bỏ /by-account
                )
                if r.status_code == 200:
                    data = r.json()
                    return {
                        "user_id": account_id,
                        "full_name": data.get("full_name", ""),
                        "email": data.get("email", ""),
                        "speaker_label": user_to_speaker.get(account_id),
                    }
                else:
                    logger.warning(
                        f"fetch_one_member {account_id}: status={r.status_code} body={r.text}"
                    )
            except Exception as e:
                logger.error(f"fetch_one_member {account_id} error: {e}")
            return None

        results = await asyncio.gather(  # ← dòng này bị mất
            *[fetch_one_member(uid) for uid in participant_user_ids]
        )

    return [r for r in results if r is not None]
