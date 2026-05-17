import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class MeetingServiceClient:
    def __init__(self):
        self.base_url = settings.MEETING_SERVICE_URL.rstrip("/")

    async def update_meeting_status(self, meeting_id: str, status: str) -> dict:
        url = f"{self.base_url}/internal/meetings/{meeting_id}/status"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.patch(url, json={"status": status})
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(
                f"Failed to update meeting status to {status} for meeting_id={meeting_id}: {e}"
            )
            return {}

meeting_service_client = MeetingServiceClient()
