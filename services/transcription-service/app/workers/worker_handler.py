import asyncio
import uuid

from app.services.deepgram_service import call_deepgram
from app.services.storage_service import get_signed_url
from app.db.database import AsyncSessionLocal
from app.repositories.job_repo import TranscriptionJobRepo


def handle_job(job_id: str):            
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_handle_job_async(job_id))
    finally:
        loop.close()


async def _handle_job_async(job_id: str):
    job_uuid = uuid.UUID(job_id)

    async with AsyncSessionLocal() as db:
        repo = TranscriptionJobRepo(db)

        job = await repo.get_by_id(job_uuid)
        if not job:
            print(f"[WARN] Job not found: {job_id}")
            return None

        await repo.update_status(job.id, "processing")

        media_file_id = str(job.media_file_id)
        model = job.model or "nova-2"
        options = job.options or {}

    media_url = get_signed_url(media_file_id)
    if not media_url:
        async with AsyncSessionLocal() as db:
            repo = TranscriptionJobRepo(db)
            await repo.update_status(job_uuid, "failed")    

        raise Exception("Cannot get signed URL")

    payload = {
        "model": model,
        "language": options.get("language_code", "vi"),
        "diarize": "true" if options.get("diarize", True) else "false",
        "punctuate": "true" if options.get("punctuate", True) else "false",
        "smart_format": "true" if options.get("smart_format", True) else "false",
    }

    try:
        result = call_deepgram(media_url, payload)
        request_id = result.get("request_id")

        print(f">>> REQUEST_ID: {request_id}")

        async with AsyncSessionLocal() as db:
            repo = TranscriptionJobRepo(db)

            job = await repo.get_by_id(job_uuid)
            if job:
                job.deepgram_request_id = request_id
                await db.commit()

        return {
            "job_id": job_id,
            "request_id": request_id
        }

    except Exception as e:
        async with AsyncSessionLocal() as db:
            repo = TranscriptionJobRepo(db)
            await repo.update_status(job_uuid, "failed")
            await db.commit()

        print(f"[ERROR] Deepgram failed: {str(e)}")
        raise