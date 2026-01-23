import os
from celery import Celery
import dotenv
# Load environment variables from .env file
dotenv.load_dotenv(dotenv.find_dotenv() )

# Determine Celery mode based on environment variable
local_mode = os.getenv("CELERY_MODE", "celery") == "local"
print(f"Celery mode set to: {'local' if local_mode else 'celery'}")

# Initialize Celery
if local_mode:
    broker_url = "memory://"
    result_backend = "cache+memory://"
else:
    broker_url = "redis://localhost:6379/0"
    result_backend = "redis://localhost:6379/0"

celery_app = Celery(
    "research_agent_api",
    broker=broker_url,
    backend=result_backend,
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_always_eager=local_mode,
    task_eager_propagates=local_mode
)

# Auto-discover tasks from the tasks folder
celery_app.autodiscover_tasks(["tasks"])