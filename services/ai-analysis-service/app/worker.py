import asyncio
import json
import logging
from datetime import datetime, timezone

from app.core.redis import redis_client, QUEUE_ANALYSIS
from app.db.database import AsyncSessionLocal
from app.core.config import settings
from app.repositories.job_repo import AnalysisJobRepo
from app.repositories.summary_repo import MeetingSummaryRepo
from app.repositories.task_repo import ExtractedTaskRepo
from app.services.groq_service import analyze_meeting
from app.services.utterance_client import fetch_utterances

logger = logging.getLogger(__name__)

CHANNEL_ANALYSIS_COMPLETED = "analysis.completed"


async def process_message(message: dict):
    async with AsyncSessionLocal() as db:
        job_repo = AnalysisJobRepo(db)
        summary_repo = MeetingSummaryRepo(db)
        task_repo = ExtractedTaskRepo(db)

        # ── 1. Lấy job từ DB ──────────────────────────────────────────────
        job_id = message.get("job_id")
        logger.info(f"[WORKER] Bắt đầu xử lý message: {message}")

        job = await job_repo.get_by_id(job_id)
        if not job:
            logger.error(f"[WORKER] Job không tồn tại: {job_id}")
            return

        logger.info(f"[WORKER] Job {job.id} — status hiện tại: {job.status}")

        # Guard: tránh xử lý lại job đã done hoặc đang processing
        if job.status in ("processing", "done"):
            logger.warning(
                f"[WORKER] Job {job.id} đã ở trạng thái {job.status}, bỏ qua"
            )
            return

        # ── 2. Cập nhật status → processing ──────────────────────────────
        await job_repo.update(
            job,
            status="processing",
            started_at=datetime.now(timezone.utc),
        )
        logger.info(f"[WORKER] Job {job.id} → processing")

        try:
            # ── 3. Fetch utterances ───────────────────────────────────────
            logger.info(
                f"[WORKER] Job {job.id} — fetch_utterances(transcript_id={job.transcript_id})"
            )
            try:
                utterances = await fetch_utterances(str(job.transcript_id))
            except Exception as e:
                raise RuntimeError(f"[fetch_utterances] {type(e).__name__}: {e}") from e

            if not utterances:
                raise ValueError(
                    f"Không có utterances cho transcript {job.transcript_id}"
                )

            logger.info(
                f"[WORKER] Job {job.id} — lấy được {len(utterances)} utterances"
            )

            # ── 4. Gọi Groq ───────────────────────────────────────────────
            logger.info(
                f"[WORKER] Job {job.id} — gọi analyze_meeting("
                f"model={job.ai_model or settings.GROQ_MODEL}, "
                f"utterances_count={len(utterances)})"
            )
            try:
                (
                    summary_data,
                    tasks_data,
                    input_tokens,
                    output_tokens,
                ) = await analyze_meeting(
                    utterances=utterances,
                    model=job.ai_model or settings.GROQ_MODEL,
                )
            except Exception as e:
                raise RuntimeError(f"[analyze_meeting] {type(e).__name__}: {e}") from e

            logger.info(
                f"[WORKER] Job {job.id} — Groq OK: "
                f"{len(tasks_data)} tasks, tokens in={input_tokens} out={output_tokens}"
            )

            # ── 5a. Lưu summary ───────────────────────────────────────────
            logger.info(f"[WORKER] Job {job.id} — lưu summary...")
            try:
                await summary_repo.create(
                    {
                        "analysis_job_id": job.id,
                        "meeting_id": job.meeting_id,
                        **summary_data,
                    }
                )
            except Exception as e:
                raise RuntimeError(
                    f"[summary_repo.create] {type(e).__name__}: {e}"
                ) from e
            logger.info(f"[WORKER] Job {job.id} — đã lưu summary")

            # ── 5b. Lưu tasks ─────────────────────────────────────────────
            if tasks_data:
                logger.info(f"[WORKER] Job {job.id} — lưu {len(tasks_data)} tasks...")
                try:
                    await task_repo.bulk_create(
                        [
                            {
                                "analysis_job_id": job.id,
                                "meeting_id": job.meeting_id,
                                **task,
                            }
                            for task in tasks_data
                        ]
                    )
                except Exception as e:
                    raise RuntimeError(
                        f"[task_repo.bulk_create] {type(e).__name__}: {e}"
                    ) from e
                logger.info(f"[WORKER] Job {job.id} — đã lưu {len(tasks_data)} tasks")
            else:
                logger.info(f"[WORKER] Job {job.id} — không có task nào")

            # ── 6. Cập nhật job → done ────────────────────────────────────
            await job_repo.update(
                job,
                status="done",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                completed_at=datetime.now(timezone.utc),
            )
            logger.info(f"[WORKER] Job {job.id} → done ✓")

            # ── 7. Publish event ───────────────────────────────────────────
            event_payload = {
                "event": "analysis.completed",
                "job_id": str(job.id),
                "meeting_id": str(job.meeting_id),
                "transcript_id": str(job.transcript_id),
                "task_count": len(tasks_data),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            try:
                await redis_client.publish(
                    CHANNEL_ANALYSIS_COMPLETED,
                    json.dumps(event_payload),
                )
            except Exception as e:
                # Không fail job chỉ vì publish lỗi
                logger.warning(f"[WORKER] Job {job.id} — publish event thất bại: {e}")

            logger.info(f"[WORKER] Published analysis.completed event cho job {job.id}")

        except Exception as e:
            logger.error(
                f"[WORKER] Job {job.id} FAILED ở bước: {e}",
                exc_info=True,  # In full traceback
            )
            await job_repo.update(
                job,
                status="failed",
                error_message=str(e),
            )


async def run_worker():
    logger.info(f"[WORKER] AI Analysis Worker started — listening: {QUEUE_ANALYSIS}")
    while True:
        try:
            result = await redis_client.brpop(QUEUE_ANALYSIS, timeout=5)
            if result:
                _, raw = result
                logger.debug(f"[WORKER] Raw message nhận được: {raw}")
                message = json.loads(raw)
                logger.info(f"[WORKER] Dequeue message: {message}")
                await process_message(message)
        except Exception as e:
            logger.error(
                f"[WORKER] Worker loop error: {type(e).__name__}: {e}", exc_info=True
            )
            await asyncio.sleep(2)
