from datetime import datetime

import logging
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