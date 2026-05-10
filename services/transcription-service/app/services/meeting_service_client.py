import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class MeetingServiceClient:
    def __init__(self):
        self.base_url = settings.MEETING_SERVICE_URL.rstrip("/")

    async def get_meeting(self, meeting_id: str) -> dict:
        url = f"{self.base_url}/internal/meetings/{meeting_id}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Meeting service returned {e.response.status_code} "
                f"for meeting_id={meeting_id}"
            )
            raise
        except Exception as e:
            logger.error(
                f"Failed to call meeting service for meeting_id={meeting_id}: {e}"
            )
            raise


meeting_service_client = MeetingServiceClient()
