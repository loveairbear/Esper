from kin.messaging.slack_messenger import SlackMessenger
from kin.scheduling.celery_tasks import startupday1
from os import environ
token = environ.get('SLACK_API')
startupday1.delay(token, '@imranahmed')
