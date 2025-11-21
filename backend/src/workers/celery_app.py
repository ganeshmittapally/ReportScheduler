"""Celery application configuration."""

import logging
from celery import Celery
from kombu import Exchange, Queue

from src.config import settings

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "reportscheduler",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution settings
    task_acks_late=True,  # Acknowledge after task completion
    task_reject_on_worker_lost=True,  # Reject task if worker crashes
    task_track_started=True,  # Track when task starts
    
    # Result backend settings
    result_expires=86400,  # Results expire after 24 hours
    result_persistent=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,  # Prefetch one task at a time for fair distribution
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks (prevent memory leaks)
    
    # Task routing
    task_routes={
        "src.workers.tasks.generate_report": {"queue": "reports"},
        "src.workers.tasks.send_email": {"queue": "notifications"},
    },
    
    # Queue definitions
    task_queues=(
        Queue(
            "reports",
            Exchange("reports"),
            routing_key="reports",
            queue_arguments={"x-max-priority": 10},  # Enable priority queue
        ),
        Queue(
            "notifications",
            Exchange("notifications"),
            routing_key="notifications",
        ),
    ),
    
    # Task time limits
    task_soft_time_limit=300,  # 5 minutes soft limit (raises exception)
    task_time_limit=600,  # 10 minutes hard limit (kills task)
    
    # Retry settings
    task_default_retry_delay=60,  # Retry after 60 seconds
    task_max_retries=3,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["src.workers"])

logger.info("Celery app configured successfully")
