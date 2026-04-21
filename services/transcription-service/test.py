from dotenv import load_dotenv
load_dotenv()

from app.workers.tasks import process_transcription

JOB_ID = "cc2ffff3-a034-4e19-9593-d7c6b4f7cc23"

def test_celery():
    print("🚀 Sending job to Celery...")

    task = process_transcription.delay(JOB_ID)

    print("✅ Task ID:", task.id)
    print("📌 Status:", task.status)

if __name__ == "__main__":
    test_celery()