from dotenv import load_dotenv

load_dotenv()

from app.workers.tasks import process_transcription

JOB_ID = "27a80075-8834-4210-bc48-d0af890d1b2e"


def test_celery():
    print("🚀 Sending job to Celery...")

    task = process_transcription.delay(JOB_ID)

    print("✅ Task ID:", task.id)
    print("📌 Status:", task.status)


if __name__ == "__main__":
    test_celery()
