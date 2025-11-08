from celery import Celery
from celery.schedules import crontab
import structlog

from app.core.config import settings

logger = structlog.get_logger()

# Create Celery instance
celery_app = Celery(
    "flowmind",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.ai_tasks",
        "app.tasks.notification_tasks",
        "app.tasks.sync_tasks",
        "app.tasks.analytics_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Periodic tasks
celery_app.conf.beat_schedule = {
    # AI-powered productivity insights (daily)
    "generate-daily-insights": {
        "task": "app.tasks.ai_tasks.generate_daily_productivity_insights",
        "schedule": crontab(hour=8, minute=0),  # 8 AM daily
    },
    
    # Send due task reminders (every 15 minutes)
    "send-task-reminders": {
        "task": "app.tasks.notification_tasks.send_task_due_reminders",
        "schedule": crontab(minute="*/15"),
    },
    
    # Sync external calendars (every 5 minutes)
    "sync-calendars": {
        "task": "app.tasks.sync_tasks.sync_external_calendars",
        "schedule": crontab(minute="*/5"),
    },
    
    # Process meeting recordings (every 10 minutes)
    "process-meeting-recordings": {
        "task": "app.tasks.ai_tasks.process_meeting_recordings",
        "schedule": crontab(minute="*/10"),
    },
    
    # Update productivity metrics (hourly)
    "update-productivity-metrics": {
        "task": "app.tasks.analytics_tasks.update_hourly_metrics",
        "schedule": crontab(minute=0),  # Every hour
    },
    
    # Clean up old notifications (daily)
    "cleanup-old-notifications": {
        "task": "app.tasks.notification_tasks.cleanup_old_notifications",
        "schedule": crontab(hour=2, minute=0),  # 2 AM daily
    },
    
    # Generate weekly reports (Mondays at 9 AM)
    "generate-weekly-reports": {
        "task": "app.tasks.analytics_tasks.generate_weekly_reports",
        "schedule": crontab(hour=9, minute=0, day_of_week=1),
    },
    
    # AI schedule optimization (every 30 minutes during work hours)
    "optimize-schedules": {
        "task": "app.tasks.ai_tasks.optimize_user_schedules",
        "schedule": crontab(minute="*/30", hour="8-18"),
    },
    
    # Backup user data (daily at 3 AM)
    "backup-user-data": {
        "task": "app.tasks.maintenance_tasks.backup_user_data",
        "schedule": crontab(hour=3, minute=0),
    },
}
