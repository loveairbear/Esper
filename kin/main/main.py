from kin.scheduling.celery_tasks import startupday1
from kin.messaging.slack_messenger import SlackMessenger
from datetime import datetime, timedelta
from pytz import timezone

BOTS = set()

class StartupBot:

    def __init__(self, token):
        self.token = token
        self.bot = SlackMessenger(token)

    def run(self):
        user = self.bot.userlist['@imranahmed']
        print(self.bot.userlist['@imranahmed'])
        self.bot.say(
            'hey! this the startupbot that is being developed as we speak',user['user_id'])
        tz = user['timezone']
        a = datetime.now(timezone(tz))
        # make a timezone aware date
        b = datetime(a.year, a.month, a.day + 1, 9, 0, 0, 0, timezone(tz))
        c = b - a
        #schedule the first message
        #startupday1.async_delay([self.bot, user], datetime.now(timezone(tz)) + c)
