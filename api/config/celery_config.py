from celery import Celery

# Initialize Celery
celery_app = Celery(
    "my_api",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
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
)

# Auto-discover tasks from the tasks folder
celery_app.autodiscover_tasks(["tasks"])