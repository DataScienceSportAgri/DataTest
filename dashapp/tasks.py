# Dans tasks.py
from celery import shared_task

@shared_task
def scheduled_delete_points():
    from dashapp.models import delete_all_points
    delete_all_points()

# Dans settings.py
CELERY_BEAT_SCHEDULE = {
    'delete-points-hourly': {
        'task': 'myapp.tasks.scheduled_delete_points',
        'schedule': 3600.0,  # 3600 secondes = 1 heure
    },
}