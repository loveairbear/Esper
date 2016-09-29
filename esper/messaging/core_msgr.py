from datetime import datetime
import requests
import logging
from os import environ
import json
import redis
logger = logging.getLogger(__name__)

class Conv1:
    def __init__(self,redis):

    
class Conversation:

    """
    An object to track and organize a conversation
    """
    _instances = []

    def __init__(self, init_msg, fbid, to_send):
        self.fbid = fbid
        self.tobesaved = []
        self.start_time = datetime.utcnow()
        self.seq_out = 0
        self.seq_in = 0
        self.tosend = to_send
        self.last_active = datetime.fromtimestamp(init_msg['timestamp'] / 1000)
        if self.get_instance(fbid):
            raise ValueError(
                'An instance with fbid: {} already exists'.format(fbid))
        self._instances.append(self)

    def __contains__(self, item):
        if item == self.fbid:
            return True

    def next(self, func_say):
        self.track_out(self.tosend[self.seq_out])
        return self.tosend[self.seq_out]
    def no_response(self):
        rcvd_time = datetime.utcnow()
        if self.tosend[self.seq_in]['options']['capture']:
            


    def track_in(self, msg):
        # Store received message in transcript
        stamp = msg.get('timestamp')
        rcvd_time = datetime.utcfromtimestamp(stamp / 1000)
        if self.tosend[self.seq_in]['options']['capture']:
            # get fbid
            # add to db
            self.tobesaved.append((rcvd_time,
                                   self.tosend[seq_in],
                                   msg))
            pass
        self.seq_in += 1

        self.last_active = rcvd_time

    def track_out(self, msg_out):
        self.seq_out += 1
        self.last_active = datetime.utcnow()

    @classmethod
    def list_instances(self):
        return self._instances

    @classmethod
    def get_instance(self, fbid):
        instances = self.list_instances()
        for obj in instances:
            if fbid in obj:
                return obj
        return None

    @classmethod
    def decayed(self, obj):
        time_diff = (datetime.utcnow() - obj.last_active)
        return time_diff.seconds/60 > 30

    @classmethod
    def decayed_instances(self):
        # archive capture object
        inactive,active = [], []
        for inst in self._instances:
            (active,inactive)[1 if self.decayed(inst) else 0].append(inst)

        self._instances = active
        return inactive




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
