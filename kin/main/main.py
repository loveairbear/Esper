
from kin.messaging.slack_msgr import SlackMessenger
from kin.messaging.fb_msgr import FbMessenger
from kin.database.models import TeamCredits
from datetime import datetime, timedelta
from pytz import timezone


def retrievebots():
    teams = set()
    for team in TeamCredits.objects():
        teams.add(team)
    return teams


class StartupBot:

    def __init__(self, token):
        self.token = token
        self.bot = SlackMessenger(token)

    def run(self):
        self.bot.rtm_async()
        for user in self.bot.userlist:
            #tz = user['timezone']
            #now = datetime.now(timezone(tz))
            # make a timezone aware date
            #future = now.replace(hour=14, minute=28)
            # a.replace(day = a.day + 1,hour=9,minute=0)
            # schedule the first message for
            self.bot.say(
                'Startup bot dev mode is ready, type "ready" to start 10 days of doom',
                 user)
        # print(self.bot.rtm_sync(user['username']))
        # startupday1.apply_async(args=[self.bot, user['user_id']],
        #                        eta=future)
