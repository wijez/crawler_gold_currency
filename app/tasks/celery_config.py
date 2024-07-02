from celery import Celery
from app.core import get_settings
from celery.schedules import crontab
from kombu import Exchange, Queue

settings = get_settings()

celery_app = Celery(
    'gold_service',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.task"]
)
celery_app.autodiscover_tasks(['app.tasks.task'])

celery_app.conf.update(
    result_expires=3600,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    broker_connection_retry_on_startup=True,
    timezone='Asia/Ho_Chi_Minh',
    enable_utc=True,
)


celery_app.conf.beat_schedule = {
    'fetch_and_send_email_every_2_minutes': {
        'task': 'app.tasks.task.send_email_task_celery',
        'schedule': crontab(minute="*/2"),
    },
}
celery_app.conf.task_queues = (
    Queue('default', Exchange('default'), routing_key='default'),
    Queue('emails', Exchange('emails'), routing_key='email.send')
)

celery_app.conf.broker_transport_options = {'visibility_timeout': 10}
celery_app.conf.task_default_queue = 'default'
celery_app.conf.task_default_exchange_type = 'direct'
celery_app.conf.task_default_routing_key = 'default'


@celery_app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
