from celery import Celery
from datetime import datetime, timedelta
from pytz import timezone
from os import environ


celeryapp = Celery('celery_tasks', broker=environ.get('AMQP_URL'))

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

# how to start a startup

@celeryapp.task
def test(bot,user):
    bot.say('test1!!',user)



@celeryapp.task
def startupday1(bot, user):
    user_info = bot.userlist[user]
    bot.say('day1', user)
    eta = datetime.now(timezone(user_info['timezone'])) + timedelta(minutes=2)
    startupday2.apply_async([bot, user], eta=eta)


@celeryapp.task
def startupday2(bot, user):
    user_info = bot.userlist[user]
    bot.say('day2', user)
    eta = datetime.now(timezone(user_info['timezone'])) + timedelta(minutes=2)
    startupday3.apply_async([bot, user], eta=eta)


@celeryapp.task
def startupday3(bot, user):
    user_info = bot.userlist[user]
    bot.say('day3', user)
    eta = datetime.now(timezone(user_info['timezone'])) + timedelta(minutes=2)
    startupday4.apply_async([bot, user], eta=eta)


@celeryapp.task
def startupday4(bot, user):
    user_info = bot.userlist[user]
    bot.say('day4', user)
    eta = datetime.now(timezone(user_info['timezone'])) + timedelta(minutes=2)
    startupday5.apply_async([bot, user], eta=eta)


@celeryapp.task
def startupday5(bot, user):
    user_info = bot.userlist[user]
    bot.say('day5', user)
    eta = datetime.now(timezone(user_info['timezone'])) + timedelta(minutes=2)
    startupday6.apply_async([bot, user], eta=eta)


@celeryapp.task
def startupday6(bot, user):
    user_info = bot.userlist[user]
    bot.say('day6', user)
    eta = datetime.now(timezone(user_info['timezone'])) + timedelta(minutes=2)
    startupday7.apply_async([bot, user], eta=eta)


@celeryapp.task
def startupday7(bot, user):
    user_info = bot.userlist[user]
    bot.say('day7', user)
    eta = datetime.now(timezone(user_info['timezone'])) + timedelta(minutes=2)
    startupday8.apply_async([bot, user], eta=eta)


@celeryapp.task
def startupday8(bot, user):
    user_info = bot.userlist[user]
    bot.say('day8', user)
    eta = datetime.now(timezone(user_info['timezone'])) + timedelta(minutes=2)
    startupday9.apply_async([bot, user], eta=eta)


@celeryapp.task
def startupday9(bot, user):
    user_info = bot.userlist[user]
    bot.say('day9', user)
    eta = datetime.now(timezone(user_info['timezone'])) + timedelta(minutes=2)
    startupday10.apply_async([bot, user], eta=eta)


@celeryapp.task
def startupday10(bot, user):
    bot.say('last day!', user)
