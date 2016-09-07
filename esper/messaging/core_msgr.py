from datetime import datetime
import requests
import logging
from os import environ
import json
logger = logging.getLogger(__name__)


class Conversation:

    """
    An object to track and organize a conversation
    """

    def __init__(self, msgr, send_msgs):
        self.msgr = msgr
        self.transcript = []
        self.sendmsgs = send_msgs
        self.start_time = datetime.now()
        self.last_active = datetime.now()
        self.type = None

    def next(self, func_say):
        func_say(next(self.send_msgs))

    def received(self, msg):
        ''' Store received message in transcript'''
        self.transcript.append((msg, datetime.now()))
        self.last_active = datetime.now()




def track(recipient, msg):
    send = json.dumps({
        "message": msg,
        "recipient": recipient,
        "token": environ.get("ANALYTICS"),
        "timestamp": datetime.utcnow().timestamp()
    })

    status = requests.post(url="http://botanalytics.co/api/v1/track",
                  headers={"Content-Type": "application/json"},
                  data=send)
    return status


def track_user(user_info, user_id):
    user_info['token'] = environ.get('ANALYTICS')
    user_info['user_id'] = user_id
    status = requests.post(url="http://botanalytics.co/api/v1/engage",
                           headers={"Content-Type": "application/json"},
                           data=json.dumps(user_info))
    return status
