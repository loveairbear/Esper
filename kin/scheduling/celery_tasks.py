from celery import Celery
from kin.messaging.slack_messenger import SlackMessenger
from datetime import datetime, timedelta
from pytz import timezone
from os import environ

AVATAR = 'https://s-media-cache-ak0.pinimg.com/736x/bc/a3/67/bca3678bf9df255f9be2c9efed8ec24a.jpg'
kin = SlackMessenger('zenfer', AVATAR, environ.get('SLACK_API'))
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
def startupday1(team_token, user):
    bot = SlackMessenger('zenfer', AVATAR, team_token)
    user_info = bot.userlist[user]
    bot.say('day1', user)
    eta = datetime.now(timezone(user_info['timezone']) + timedelta(minute=2))
    startupday2.apply_async(team_token, user, eta=eta)


@celeryapp.task
def startupday2(team_token, user):

    bot = SlackMessenger('zenfer', AVATAR, team_token)
    user_info = bot.userlist[user]
    bot.say('day2', user)
    eta = datetime.now(timezone(user_info['timezone']) + timedelta(minute=2))
    startupday3.apply_async(team_token, user, eta=eta)


@celeryapp.task
def startupday3(team_token, user):

    bot = SlackMessenger('zenfer', AVATAR, team_token)
    user_info = bot.userlist[user]
    bot.say('day3', user)
    eta = datetime.now(timezone(user_info['timezone']) + timedelta(minute=2))
    startupday4.apply_async(team_token, user, eta=eta)


@celeryapp.task
def startupday4(team_token, user):

    bot = SlackMessenger('zenfer', AVATAR, team_token)
    user_info = bot.userlist[user]
    bot.say('day4', user)
    eta = datetime.now(timezone(user_info['timezone']) + timedelta(minute=2))
    startupday5.apply_async(team_token, user, eta=eta)


@celeryapp.task
def startupday5(team_token, user):

    bot = SlackMessenger('zenfer', AVATAR, team_token)
    user_info = bot.userlist[user]
    bot.say('day5', user)
    eta = datetime.now(timezone(user_info['timezone']) + timedelta(minute=2))
    startupday6.apply_async(team_token, user, eta=eta)


@celeryapp.task
def startupday6(team_token, user):

    bot = SlackMessenger('zenfer', AVATAR, team_token)
    user_info = bot.userlist[user]
    bot.say('day6', user)
    eta = datetime.now(timezone(user_info['timezone']) + timedelta(minute=2))
    startupday7.apply_async(team_token, user, eta=eta)


@celeryapp.task
def startupday7(team_token, user):

    bot = SlackMessenger('zenfer', AVATAR, team_token)
    user_info = bot.userlist[user]
    bot.say('day7', user)
    eta = datetime.now(timezone(user_info['timezone']) + timedelta(minute=2))
    startupday8.apply_async(team_token, user, eta=eta)


@celeryapp.task
def startupday8(team_token, user):

    bot = SlackMessenger('zenfer', AVATAR, team_token)
    user_info = bot.userlist[user]
    bot.say('day8', user)
    eta = datetime.now(timezone(user_info['timezone']) + timedelta(minute=2))
    startupday9.apply_async(team_token, user, eta=eta)


@celeryapp.task
def startupday9(team_token, user):

    bot = SlackMessenger('zenfer', AVATAR, team_token)
    user_info = bot.userlist[user]
    bot.say('day9', user)
    eta = datetime.now(timezone(user_info['timezone']) + timedelta(minute=2))
    startupday10.apply_async(team_token, user, eta=eta)


@celeryapp.task
def startupday10(team_token, user):
    bot = SlackMessenger('zenfer', AVATAR, team_token)
    bot.say('last day!', user)

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
