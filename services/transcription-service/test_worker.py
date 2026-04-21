from dotenv import load_dotenv
load_dotenv()

from app.workers.worker_handler import handle_job

result = handle_job("c3810940-0c73-427e-9fdc-ec4f16031f7c")

print("Result:", result)