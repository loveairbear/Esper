from time import time
import json
import websocket
import threading
from kin.scheduling.timezone_manage import utc_to_tz
from slacker import Slacker
from os import environ

class SlackMessenger(Slacker):

    def __init__(self, slack_api, name='startupbot', avatar='none'):
        super().__init__(slack_api)
        self.name = name
        self.avatar = avatar
        self.userlist = self._generate_userlist()
        self.sync_listen = False
        self.team_id = self.auth.test().body['team_id']

    def say(self, text, channel):
        self.chat.post_message(
            text=text, channel=channel, as_user=self.name,
            icon_url=self.avatar, unfurl_media='true', unfurl_links='true')

    def post(self, text, board):
        self.chat.post_message(
            text=text, channel=board, username=self.name,
            icon_url=self.avatar, unfurl_media=True, unfurl_links=True)

    def _on_message(self, ws, json_payload):
        payload = json.loads(json_payload)
        cond1 = "message" in payload['type']
        if cond1:
            cond2 = self.id not in payload['user']  # ignore own msgs
            cond3 = not self.sync_listen  # check if sync is on
            if cond2 and cond3:

                self.say("wassup", payload['channel'])

    def rtm_async(self):

        rtm = self.rtm.start().body
        websock_url = rtm['url']
        self.id = rtm['self']['id']  # get ID of the bot
        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(websock_url,
                                         on_message=self._on_message)
        wst = threading.Thread(target=self.ws.run_forever)
        wst.daemon = True
        wst.start()

    def rtm_sync(self, channel):
        websock_url = self.rtm.start().body['url']
        wsocket = websocket.create_connection(websock_url)

        user_channel = self.userlist[channel]['dm_channel']
        user_id = self.userlist[channel]['user_id']

        # Flag to for async websocket to ignore message
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
                        {'user_id': user_id1,
                         'dm_channel': im['id'],
                         'real_name': user['real_name'],
                         'email': user['profile']['email'],
                         # divide tz_offset by seconds in an hour
                         'tz_offset': user['tz_offset'] / 3600,
                         'timezone': utc_to_tz(user['tz_offset'] / 3600)
                         }
                    }
                    userlist.update(user_dict)
        return userlist


