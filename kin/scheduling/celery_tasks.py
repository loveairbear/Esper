from celery import Celery
from kin.messaging.slack_messenger import SlackMessenger
from datetime import datetime
from pytz import timezone
from os import environ

TIMEZONE = 'America/Toronto'  # Needs to be specified by client
AVATAR = 'https://s-media-cache-ak0.pinimg.com/736x/bc/a3/67/bca3678bf9df255f9be2c9efed8ec24a.jpg'
kin = SlackMessenger('zenfer', AVATAR, environ.get('SLACK_API'))
celeryapp = Celery('celery_tasks', broker=environ.get('AMQP_URL'))

celeryapp.conf.update(
    CELERY_TIMEZONE=TIMEZONE,
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


@celeryapp.task
def stretch():
    kin.say("hey i think you should get up and stretch a bit?", "@imranahmed")


@celeryapp.task
def test(text):
    kin.say(text, "@imranahmed")


@celeryapp.task
def assemble_convo(pixie, phrases, channel):
    for phrase in phrases:
        pixie.say(phrase, channel)
        response = pixie.rtm_sync(channel)  # returns a tuple of (text,ignored)
        if(response[1]):
            pixie.say("got ur msg")
        else:
            pixie.say("didnt get ur msg")
