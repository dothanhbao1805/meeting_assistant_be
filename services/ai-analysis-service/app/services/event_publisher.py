import json
import logging
import uuid
from datetime import datetime, timezone

from app.core.redis import redis_client

logger = logging.getLogger(__name__)

CHANNEL_ANALYSIS_COMPLETED = "analysis.completed"


async def publish_analysis_completed(
    *,
    analysis_job_id: uuid.UUID,
    meeting_id: uuid.UUID,
    transcript_id: uuid.UUID,
    summary_id: uuid.UUID | None,
    extracted_task_count: int,
    mapped_task_count: int,
) -> None:
    payload = {
        "event": CHANNEL_ANALYSIS_COMPLETED,
        "analysis_job_id": str(analysis_job_id),
        "meeting_id": str(meeting_id),
        "transcript_id": str(transcript_id),
        "summary_id": str(summary_id) if summary_id else None,
        "extracted_task_count": extracted_task_count,
        "mapped_task_count": mapped_task_count,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    await redis_client.publish(CHANNEL_ANALYSIS_COMPLETED, json.dumps(payload))
    logger.info(
        "Published analysis.completed event",
        extra={
            "analysis_job_id": str(analysis_job_id),
            "meeting_id": str(meeting_id),
            "extracted_task_count": extracted_task_count,
        },
    )
