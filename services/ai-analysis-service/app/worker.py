import asyncio
import json
import logging
from datetime import datetime, timezone, date

from app.core.redis import redis_client, QUEUE_ANALYSIS
from app.db.database import AsyncSessionLocal
from app.repositories.job_repo import AnalysisJobRepo
from app.repositories.summary_repo import MeetingSummaryRepo
from app.repositories.task_repo import ExtractedTaskRepo
from app.services.groq_service import analyze_meeting
from app.services.utterance_client import fetch_utterances
from app.services.participant_client import fetch_participants
from app.services.assignee_mapper import map_assignees
from app.services.deadline_parser import parse_deadline
from app.services.event_publisher import publish_analysis_completed

logger = logging.getLogger(__name__)

WORD_TO_NUM = {
    "một": 1,
    "hai": 2,
    "ba": 3,
    "bốn": 4,
    "năm": 5,
    "sáu": 6,
    "bảy": 7,
    "tám": 8,
    "chín": 9,
    "mười": 10,
}

FILLER_WORDS = ["vòng", "khoảng", "trong", "tầm", "chừng", "khoảng chừng"]


def normalize_deadline(text: str) -> str:
    if not text:
        return text
    result = text.lower().strip()
    for word in FILLER_WORDS:
        result = result.replace(word, "").strip()
    for word, num in WORD_TO_NUM.items():
        result = result.replace(word, str(num))
    return result.strip()


async def process_message(message: dict):
    async with AsyncSessionLocal() as db:
        job_repo = AnalysisJobRepo(db)
        summary_repo = MeetingSummaryRepo(db)
        task_repo = ExtractedTaskRepo(db)

        job = await job_repo.get_by_id(message["job_id"])
        if not job:
            logger.error(f"Job không tồn tại: {message['job_id']}")
            return

        await job_repo.update(
            job, status="processing", started_at=datetime.now(timezone.utc)
        )

        try:
            # 1. Lấy utterances từ Transcription Service
            utterances = await fetch_utterances(str(job.transcript_id))
            if not utterances:
                raise ValueError("Không có utterances để phân tích")

            # 2. Lấy participants (user_id + full_name) từ Meeting + Company Service
            participants = await fetch_participants(
                str(job.meeting_id), str(job.transcript_id)
            )
            logger.info(f"[DEBUG] Participants ({len(participants)}): {participants}")

            # 3. Gọi Groq song song: summary + task extraction
            (
                summary_data,
                tasks_data,
                input_tokens,
                output_tokens,
            ) = await analyze_meeting(
                utterances=utterances,
                model=job.ai_model,
                participants=participants,
            )
            logger.info(
                f"[DEBUG] Tasks từ Groq: {json.dumps(tasks_data, ensure_ascii=False)}"
            )

            # 4. AI tự map assignee_name → resolved_user_id
            tasks_data = map_assignees(tasks_data, participants)
            logger.info(
                f"[DEBUG] Tasks sau map: {[(t['title'], t.get('raw_assignee_text'), t.get('resolved_user_id')) for t in tasks_data]}"
            )

            # 5. Normalize + parse deadline_raw → deadline_date
            ref_date = date.today()
            for task in tasks_data:
                raw = task.get("deadline_raw")
                normalized = normalize_deadline(raw)
                task["deadline_date"] = parse_deadline(normalized, ref_date)

            # Log kết quả map
            for t in tasks_data:
                status = "✅" if t.get("resolved_user_id") else "⚠️ cần user gán"
                logger.info(
                    f"{status} Task: {t['title']} | assignee: {t.get('raw_assignee_text')} → {t.get('resolved_user_id')}"
                )

            # 6. Lưu summary
            summary = await summary_repo.create(
                {
                    "analysis_job_id": job.id,
                    "meeting_id": job.meeting_id,
                    **summary_data,
                }
            )

            # 7. Lưu tasks
            created_tasks = await task_repo.bulk_create(
                [
                    {
                        "analysis_job_id": job.id,
                        "meeting_id": job.meeting_id,
                        **task,
                    }
                    for task in tasks_data
                ]
            )

            # 8. Cập nhật job → done
            await job_repo.update(
                job,
                status="done",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                completed_at=datetime.now(timezone.utc),
            )

            mapped = sum(1 for t in tasks_data if t.get("resolved_user_id"))
            await publish_analysis_completed(
                analysis_job_id=job.id,
                meeting_id=job.meeting_id,
                transcript_id=job.transcript_id,
                summary_id=summary.id,
                extracted_task_count=len(created_tasks),
                mapped_task_count=mapped,
            )

            logger.info(
                f"Job {job.id} hoàn thành — "
                f"{len(tasks_data)} tasks, "
                f"{mapped} mapped, "
                f"{len(tasks_data) - mapped} cần user review"
            )

        except Exception as e:
            logger.error(f"Job {job.id} thất bại: {e}")
            await job_repo.update(job, status="failed", error_message=str(e))


async def run_worker():
    logger.info("AI Analysis Worker started — listening: " + QUEUE_ANALYSIS)
    while True:
        try:
            result = await redis_client.brpop(QUEUE_ANALYSIS, timeout=5)
            if result:
                _, raw = result
                message = json.loads(raw)
                await process_message(message)
        except Exception as e:
            logger.error(f"Worker error: {e}")
            await asyncio.sleep(2)
