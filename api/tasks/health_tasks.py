from config.celery_config import celery_app
import time

@celery_app.task(name="tasks.check_system_health")
def check_system_health():
    """
    Simulates a health check task that performs background operations
    """
    print("check_system_health working...")
    time.sleep(2)  # Simulate some work
    
    return {
        "status": "healthy",
        "celery_worker": "operational",
        "timestamp": time.time()
    }