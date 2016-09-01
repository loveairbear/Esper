from celery import Celery

from os import environ

celeryapp = Celery('celery_tasks', include=['esper.messaging.slack_msgr',
                                            'esper.messaging.fb_msgr'
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
    CELERY_SEND_EVENTS=True,  # Will not create celeryev.* queues
    # Will delete all celeryev. queues without consumers after 1 minute.
    CELERY_EVENT_QUEUE_EXPIRES=60,
    CELERY_ACCEPT_CONTENT=['json', 'msgpack', 'yaml', 'pickle'],
    CELERYD_HIJACK_ROOT_LOGGER=False
)

'''
  implement removing tasks for a user if stop has been requested
  """
  revoke not completed task and return revoking result
  """
  task = AsyncResult(task_id)
  if not task.ready():
    revoke(task_id, terminate=True)
    result = 'Task %s revoked' % task_id
  else:
    result = 'Can not revoke. Task %s is completed' % task_id
  data = {
    'result': result,
  }
'''