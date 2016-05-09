from kin.scheduling.celery_tasks import startupday1
from kin.messaging.slack_messenger import SlackMessenger
from datetime import datetime,timedelta
from pytz import timezone
from os import environ
token = environ.get('SLACK_API')
"""
get token from HTTP handler and create a new bot and start
"""


class StartupBot:

    def __init__(self, token):
        self.token = token
        self.bot = SlackMessenger('zenfer', 'avatard', token)

    def run(self):
        for user in self.bot.userlist:
            # self.bot.say('hey! this the startupbot that is being developed as we speak',
            #             user)
            tz = self.bot.userlist[user]['timezone']
            a = datetime.now(timezone(tz))
            b = datetime(a.year,a.month,a.day+1,9,0,0,0,timezone(tz))
            c = b-a
            print('&&&&&&&&&&&&')
            print(dir(c))
            print(datetime.now(timezone(tz)))
            print(datetime.now(timezone(tz))+c)

            # startupday1.delay(self.bot, user)

a = StartupBot(token)
if __name__ == '__main__':
    a = StartupBot(token)
    a.run()
