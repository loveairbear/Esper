
import json
import requests
from os import environ
import logging
import time
from random import randint
from datetime import datetime, timedelta
from pytz import timezone

from kin.database.models import FbUserInfo
from kin.scheduling import timezone_manage, celery_tasks

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class FbMessenger:

    '''
    FbMessenger simplified interface to send messages
    '''

    def __init__(self, fbid=None, userinfo=None, token=environ.get('FB_TOKEN')):
        self.token = token
        self.fbid = fbid
        self.user = userinfo

    def __contains__(self, item):
        if int(self.fbid) == int(item):
            return True
        else:
            return False

    def word_process(self, text):
        logger.debug('got a text:' + text)

    def say(self, text):

        post_message_url = 'https://graph.facebook.com/v2.6/me/messages?access_token={}'.format(
            self.token)
        response_msg = json.dumps(
            {"recipient": {"id": self.fbid}, "message": {"text": text}})

        status = requests.post(post_message_url,
                               headers={"Content-Type": "application/json"},
                               data=response_msg)
        time.sleep(randint(10,30))

    def send_media(self, url):
        post_message_url = 'https://graph.facebook.com/v2.6/me/messages?access_token={}'.format(
            self.token)
        response_msg = json.dumps(
            {"recipient": {"id": self.fbid},
             "message": {"attachment":
                         {'type': 'image',
                             'payload': {'url': url}
                          }
                         }
             })

        status = requests.post(post_message_url,
                               headers={"Content-Type": "application/json"},
                               data=response_msg)

    def store_user(self):
        # check if user account already exists
        get_message_url = '''https://graph.facebook.com/v2.6/{}?fields=first_name,last_name,profile_pic,locale,timezone,gender&access_token={}'''.format(
            self.fbid, self.token)

        r = requests.get(get_message_url)
        user_info = r.json()
        logger.debug(user_info)
        # update utc_offset into Olson format timezone
        # user_info['timezone'] = timezone_manage.utc_to_tz(
        #    user_info['timezone'])

        cond = str(self.fbid) not in [
            str(doc.user_id) for doc in FbUserInfo.objects(user_id=self.fbid)]

        if cond:
            logger.debug('New User Info Entry')
            entry = FbUserInfo(name=user_info['first_name'] + ' ' + user_info['last_name'],
                               timezone=user_info['timezone'],
                               gender=user_info['gender'],
                               user_id=self.fbid)
            entry.save()
        self.user = user_info
        return user_info

    def get_userinfo(self):
        '''
        Retreive user information using fbid given in instance
        return a dict with fields: name
                                   timezone
                                   gender
                                   userid
        '''

        # check if user info existing in database
        cond = str(self.fbid) in [
            str(doc.user_id) for doc in FbUserInfo.objects(user_id=self.fbid)]

        if cond:
            return(next(FbUserInfo.objects(user_id=self.fbid)))
        else:
            get_message_url = '''https://graph.facebook.com/v2.6/{}?fields=first_name,last_name,profile_pic,locale,timezone,gender&access_token={}'''.format(
                self.fbid, self.token)
            r = requests.get(get_message_url)
            user_info = r.json()
            user_info['timezone'] = timezone_manage.utc_to_tz(
                user_info['timezone'])

            logger.debug('New User Info Entry')
            entry = FbUserInfo(name=user_info['first_name'] + ' ' + user_info['last_name'],
                               timezone=user_info['timezone'],
                               gender=user_info['gender'],
                               user_id=self.fbid)
            entry.save()
            return user_info


@celery_tasks.celeryapp.task
def startupday1(userinfo):
    bot = FbMessenger(userinfo.user_id)
    convo = ['Oh shit waddup!',
    
    ('Check em, this be the startup digitutor. '
        'Like a digimon of LEARNING. We doing the '
        'standFERD CURS> to learn startupping from '
        'boss ass niggas like Sam Altman and Marc Anderseen,'
        'Y Combinator baus '),
    'dawg and a16z baus dawg, top kek breh',
    
    ('For the novice entrepreneurs - '
        'this course will provide you a '
        'quick and very valuable overview '
        'of a startup, while massively increasing '
        'your chances of success.'),
     
    ('For the experienced entrepreneurs - you might '
        'think you know all of this, but even if you do, being '),
    ('reminded of these concepts will make you a better entrepreneur. '
        'You will get some great nuggets'),
    'and eye openers.']
    for i in convo:
        bot.say(i)
    bot.send_media('http://i.imgur.com/ujzsP2v.gif')
    eta = datetime.now(timezone(userinfo['timezone']))
    future = eta.replace(day=eta.day + 1, hour=9, minute=0)
    #startupday2.apply_async(args=[userinfo], eta=eta)


@celery_tasks.celeryapp.task
def startupday2(userinfo):
    bot = FbMessenger(userinfo.user_id, userinfo)
    bot.say('day2')
    eta = datetime.now(timezone(userinfo['timezone'])) + timedelta(day=1)
    startupday3.apply_async(args=[userinfo], eta=eta)
    # startupday3.delay(fbid,userinfo)


@celery_tasks.celeryapp.task
def startupday3(userinfo):
    bot = FbMessenger(userinfo.user_id)
    bot.say('day3')
    eta = datetime.now(timezone(userinfo['timezone'])) + timedelta(day=1)
    startupday4.apply_async([userinfo], eta=eta)


@celery_tasks.celeryapp.task
def startupday4(userinfo):
    bot = FbMessenger(userinfo.user_id)
    bot.say('day4')
    eta = datetime.now(timezone(userinfo['timezone'])) + timedelta(day=1)
    startupday5.apply_async([userinfo], eta=eta)


@celery_tasks.celeryapp.task
def startupday5(userinfo):
    bot = FbMessenger(userinfo.user_id)
    bot.say('day5')
    eta = datetime.now(timezone(userinfo['timezone'])) + timedelta(day=1)
