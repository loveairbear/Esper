from time import time,sleep
import json
import websocket
import threading
from datetime import datetime, timedelta
from pytz import timezone
from kin.scheduling.timezone_manage import utc_to_tz
from kin.scheduling.celery_tasks import celeryapp
from slacker import Slacker
from os import environ


class SlackMessenger(Slacker):
    """ 
    A module to interface with Slack API
    """
    def __init__(self, slack_api, name='qinj'):
        super().__init__(slack_api)
        info = self.auth.test().body
        self.token = slack_api
        self.name = name
        self.userlist = self._generate_userlist()
        self.sync_listen = False
        self.team_id = info['team_id']
        self.userid = info['user_id']

    def say(self, text, channel):
        """
        post a message to a direct message channel 

        """
        self.chat.post_message(
            text=text, channel=channel, as_user=True,
            unfurl_media='true', unfurl_links='true')

    def post(self, text, board):
        """post message to a discussion channel"""
        self.chat.post_message(
            text=text, channel=board, as_user=self.name,
            unfurl_media='true', unfurl_links='true')

    def _on_message(self, ws, json_payload):
        payload = json.loads(json_payload)
        cond1 = "message" in payload['type']
        if cond1:
            cond2 = self.userid not in payload['user']  # ignore own msgs
            cond3 = not self.sync_listen  # check if sync is on
            cond4 = 'ready' in payload['text'].lower()
            if cond2 and cond3 and cond4:
                 # lookup user by id and check activation
                for user in self.userlist.values():
                    usrlookup = payload['user'] in user['user_id']

                    # need to figure out how to check if the 10 days are running
                    activecheck = not user['activated'] # boolean value
                    # active check is a temporary fix but needs to be applied
                    # in a persistent database since userlist will refresh
                    if usrlookup and activecheck:
                        startupday1.apply_async(args=[self.token, user['username']])
                        self.say('activated!',user['username'])
                        #user['activated'] = True


    def rtm_async(self):
        """ 
        starts a thread to passively listen for commands
        .. note:: this is really dumb, multithreading is not viable for multiple teams
        need to switch to multiprocessing as there are now shared resource
        """
        rtm = self.rtm.start().body
        websock_url = rtm['url']
        self.id = rtm['self']['id']  # get ID of the bot
        websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp(websock_url,
                                         on_message=self._on_message)
        wst = threading.Thread(target=self.ws.run_forever)
        wst.daemon = True
        wst.start()

    def rtm_sync(self, channel):
        """ blocking code to listen for response

        """
        websock_url = self.rtm.start().body['url']
        wsocket = websocket.create_connection(websock_url)
        user_channel = self.userlist[channel]['dm_channel']
        user_id = self.userlist[channel]['user_id']

        # Flag for async websocket to ignore message
        self.sync_listen = True

        # timeout after 10 minutes
        timeout = time() + 10 * 60
        while True:
            if time() > timeout:
                return (None, False)

            package = json.loads(wsocket.recv())
            type_check = package['type'] in "message"
            if type_check:
                chan_check = package['channel'] in user_channel
                usr_check = package['user'] in user_id
                if chan_check and usr_check:
                        wsocket.close()
                        self.sync_listen = False
                        return (package['text'], True)

    def _generate_userlist(self):

        userlist = {}
        im_list = self.im.list().body['ims']
        user_list = self.users.list().body['members']

        # not pythonistic code right here
        for im in im_list:
            user_id1 = im['user']
            # cross checking user_list with im_list to get complete info
            for user in user_list:
                user_id2 = user['id']
                if user_id1 == user_id2:
                    user_dict = {
                        '@' + user['name']:
                        {'username': '@' + user['name'],
                         'user_id': user_id1,
                         'dm_channel': im['id'],
                         'real_name': user['real_name'],
                         'email': user['profile']['email'],
                         # divide tz_offset by seconds in an hour
                         'tz_offset': user['tz_offset'] / 3600,
                         'timezone': utc_to_tz(user['tz_offset'] / 3600),
                         'activated': False
                         }
                    }
                    userlist.update(user_dict)
        return userlist


# DECORATORS

@celeryapp.task
def startupday1(api_key, user):
    bot = SlackMessenger(api_key)
    user_info = bot.userlist[user]
    bot.say('day1', user)

    # schedule next task for the nex day at 9am in respective timezone
    tz = user_info['timezone']
    now = datetime.now(timezone(tz))

    # uncomment in production
    #future = now.replace(day = now.day + 1,hour=9,minute=0)

    future = now + timedelta(minutes=1)
    startupday2.apply_async(args=[api_key, user], eta=future)


@celeryapp.task
def startupday2(api_key, user):
    bot = SlackMessenger(api_key)
    user_info = bot.userlist[user]
    bot.say('day2', user)
    eta = datetime.now(timezone(user_info['timezone'])) + timedelta(minutes=2)
    startupday3.apply_async([api_key, user], eta=eta)


@celeryapp.task
def startupday3(api_key, user):
    bot = SlackMessenger(api_key)
    user_info = bot.userlist[user]
    bot.say('day3', user)
    eta = datetime.now(timezone(user_info['timezone'])) + timedelta(minutes=2)
    startupday4.apply_async([api_key, user], eta=eta)


@celeryapp.task
def startupday4(api_key, user):
    bot = SlackMessenger(api_key)
    user_info = bot.userlist[user]
    bot.say('day4', user)
    eta = datetime.now(timezone(user_info['timezone'])) + timedelta(minutes=2)
    startupday5.apply_async([api_key, user], eta=eta)


@celeryapp.task
def startupday5(api_key, user):
    bot = SlackMessenger(api_key)
    user_info = bot.userlist[user]
    bot.say('day5', user)
    eta = datetime.now(timezone(user_info['timezone'])) + timedelta(minutes=2)
    startupday6.apply_async([api_key, user], eta=eta)


@celeryapp.task
def startupday6(api_key, user):
    bot = SlackMessenger(api_key)
    user_info = bot.userlist[user]
    bot.say('day6', user)
    eta = datetime.now(timezone(user_info['timezone'])) + timedelta(minutes=2)
    startupday7.apply_async([api_key, user], eta=eta)


@celeryapp.task
def startupday7(api_key, user):
    bot = SlackMessenger(api_key)
    user_info = bot.userlist[user]
    bot.say('day7', user)
    eta = datetime.now(timezone(user_info['timezone'])) + timedelta(minutes=2)
    startupday8.apply_async([api_key, user], eta=eta)


@celeryapp.task
def startupday8(api_key, user):
    bot = SlackMessenger(api_key)
    user_info = bot.userlist[user]
    bot.say('day8', user)
    eta = datetime.now(timezone(user_info['timezone'])) + timedelta(minutes=2)
    startupday9.apply_async([api_key, user], eta=eta)


@celeryapp.task
def startupday9(api_key, user):
    bot = SlackMessenger(api_key)
    user_info = bot.userlist[user]
    bot.say('day9', user)
    eta = datetime.now(timezone(user_info['timezone'])) + timedelta(minutes=2)
    startupday10.apply_async([api_key, user], eta=eta)


@celeryapp.task
def startupday10(api_key, user):
    bot = SlackMessenger(api_key)
    bot.say('last day!', user)
    bot.say('to restart just type in "ready"')

if __name__ == '__main__':
    token = environ.get('SLACK_API')
    a = SlackMessenger(token)
    #a.say('http://i.imgur.com/BLNIVhm.jpg','@imranahmed')
    print(a.userlist['@imranahmed'])
    a.rtm_async()
    sleep(60)