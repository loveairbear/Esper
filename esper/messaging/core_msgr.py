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


def track_out(msg, res):
    url = ("https://tracker.dashbot.io/track?platform=facebook&v=0.7.3-rest&type=outgoing&apiKey={}".format(
               environ.get('ANALYTICS')
           ))

    data = json.dumps({
        "qs": {"access_token": environ.get('ANALYTICS')},
        "uri": "https://graph.facebook.com/v2.6/me/messages",
        "json": msg,
        "method": "POST",
        "responseBody": json.loads(res)

    })

    status = requests.post(url=url,
                           headers={"Content-Type": "application/json"},
                           data=data)
    return status


def track_in(entries):
    url = ("https://tracker.dashbot.io/track?platform=facebook&v=0.7.3-rest&type=incoming&apiKey={}".format(
               environ.get('ANALYTICS')
           ))
    data = json.dumps(entries)

    status = requests.post(url=url,
                           headers={"Content-Type": "application/json"},
                           data=data)
    return status