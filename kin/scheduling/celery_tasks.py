from celery import Celery

from os import environ

celeryapp = Celery('celery_tasks',include=[
                    'kin.messaging.slack_messenger'

                    ], broker=environ.get('AMQP_URL'))

celeryapp.conf.update(
    CELERY_TIMEZONE='UTC',
    CELERY_MONGODB_SCHEDULER_DB="pixie",
    CELERY_MONGODB_SCHEDULER_COLLECTION="schedules",
    CELERY_MONGODB_SCHEDULER_URL=environ.get('MONGODB_URI'),
    BROKER_POOL_LIMIT=1,  # Will decrease connection usage
    BROKER_HEARTBEAT=None,  # We're using TCP keep-alive instead
    # May require a long timeout due to Linux DNS timeouts etc
    BROKER_CONNECTION_TIMEOUT=60,
    CELERY_SEND_EVENTS=False,  # Will not create celeryev.* queues
    # Will delete all celeryev. queues without consumers after 1 minute.
    CELERY_EVENT_QUEUE_EXPIRES=60,
    CELERY_ACCEPT_CONTENT=['json', 'msgpack', 'yaml', 'pickle']
)
