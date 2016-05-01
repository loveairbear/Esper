import time
import json
import websocket
import threading
from slacker import Slacker
from os import environ

AVATAR = 'https://s-media-cache-ak0.pinimg.com/736x/bc/a3/67/bca3678bf9df255f9be2c9efed8ec24a.jpg'


class SlackMessenger:

    def __init__(self, name, avatar, slack_api):
        self.name = name
        self.avatar = avatar
        self.slackAPI = Slacker(slack_api)
        self.userlist = self._generate_userlist()
        self.sync_listen = False

    def say(self, text, channel):
        self. slackAPI.chat.post_message(
            text=text, channel=channel, as_user=self.name,
            icon_url=self.avatar, unfurl_media='true', unfurl_links='true')

    def post(self, text, board):
        self.slackAPI.chat.post_message(
            text=text, channel=board, username=self.name,
            icon_url=self.avatar, unfurl_media=True, unfurl_links=True)

    def _on_message(self, ws, json_payload):
        # print(dir(ws))
        payload = json.loads(json_payload)
        cond1 = "message" in payload['type']
        if cond1:
            cond2 = self.id not in payload['user']  # ignore own msgs
            cond3 = not self.sync_listen  # check if sync is on
            if cond2 and cond3:

                self.say("wassup", payload['channel'])

    def rtm_async(self):

        rtm = self.slackAPI.rtm.start().body
        websock_url = rtm['url']
        self.id = rtm['self']['id']  # get ID of the bot
        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(websock_url,
                                         on_message=self._on_message)
        wst = threading.Thread(target=self.ws.run_forever)
        wst.daemon = True
        wst.start()

    def rtm_sync(self, channel):
        websock_url = self.slackAPI.rtm.start().body['url']
        wsocket = websocket.create_connection(websock_url)

        user_channel = self.userlist[channel]['dm_channel']
        user_id = self.userlist[channel]['user_id']

        # Flag to for async websocket to ignore message
        self.sync_listen = True

        # timeout after 10 minutes
        timeout = time.time() + 10 * 60
        while True:
            if time.time() > timeout:
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
        im_list = self.slackAPI.im.list().body['ims']
        user_list = self.slackAPI.users.list().body['members']
        for im in range(len(im_list)):
            user_id1 = im_list[im]['user']
            # cross checking user_list with im_list to get complete info
            for m in range(len(user_list)):
                user_id2 = user_list[m]['id']
                if user_id1 == user_id2:
                    member = user_list[m]
                    user_dict = {
                        '@' + member['name']:
                        {'user_id': user_id1,
                         'dm_channel': im_list[im]['id'],
                         'real_name': member['real_name'],
                         'email': member['profile']['email']
                         }
                    }
                    userlist.update(user_dict)
        return userlist


if __name__ == '__main__':
    pass

    