# api/routes/health.py
from fastapi import APIRouter
from tasks.health_tasks import check_system_health

router = APIRouter()

@router.get("/status")
def health_check():
    """
    Health check endpoint that triggers a Celery task
    """
    # Trigger async Celery task
    task = check_system_health.delay()
    
    return {
        "status": "ok",
        "message": "API is running",
        "celery_task_id": task.id,
        "celery_task_status": task.state
    }

@router.get("/task/{task_id}")
def get_task_status(task_id: str):
    """
    Check the status of a Celery task
    """
    from celery.result import AsyncResult
    from config.celery_config import celery_app
    
    task = AsyncResult(task_id, app=celery_app)
    
    if task.ready():
        return {
            "task_id": task_id,
            "status": task.state,
            "result": task.result
        }
    else:
        return {
            "task_id": task_id,
            "status": task.state,
            "result": None
        }