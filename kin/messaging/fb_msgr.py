import json
import requests
from os import environ
import logging
import time
from random import randint, choice
from datetime import datetime, timedelta
from pytz import timezone


from kin.database import models as db
from kin.scheduling import tz_mgmt, celery_tasks


logger = logging.getLogger(__name__)


class FbMessenger:

    '''
    FbMessenger simplified interface to send messages
    '''

    def __init__(self, fbid=None, userinfo=None, token=environ.get('FB_TOKEN')):
        self.token = token
        self.fbid = fbid
        self.user = userinfo
        self.post_message_url = 'https://graph.facebook.com/v2.6/me/messages?access_token={}'.format(
            self.token)
        self._typing_indicate('typing_on')

    def __contains__(self, item):
        if int(self.fbid) == int(item):
            return True
        else:
            return False

    def send(self, payload, delay=True, **kwargs):
        '''
        method to send any type of message, media urls are automatically
        opened and sent.
        '''

        cond = payload.startswith('http')

        img_sfix = ['.gif', '.png', '.jpg']
        img_cond = any([sfix in payload for sfix in img_sfix])

        vid_sfix = ['.mp4', '.gifv']
        vid_cond = any([sfix in payload for sfix in vid_sfix])

        if img_cond and cond:
            self.send_media(payload, 'image', **kwargs)
        elif vid_cond and cond:
            self.send_media(payload, 'video', **kwargs)
        elif '.mp3' in payload and cond:
            self.send_media(payload, 'audio', **kwargs)
        else:
            # send a normal text
            self.say(payload, True, **kwargs)

    def say(self, text, delay=True, **kwargs):
        '''
        send a text message to the user defined in FbMessenger object
        params: text: message to send,
                delay: randomized delay times after messages
                **kwargs: quickreplies, metadata, etc...

        '''

        if delay:
            time.sleep(randint(1, 5))

        response_msg = dict(
            {"recipient": {"id": self.fbid},
             "message": {"text": text}
             })

        # append optional parameters to post form such as quick replies
        response_msg['message'].update(**kwargs)
        status = requests.post(self.post_message_url,
                               headers={"Content-Type": "application/json"},
                               data=json.dumps(response_msg))
        logger.debug("text message sent: {}".format(status.text))

    def _typing_indicate(self, state):
        if state:
            typing_state = 'typing_on'
        elif not state:
            typing_state = 'typing_off'
        else:
            typing_state = 'mark_seen'
        response_msg = json.dumps(
            {"recipient": {"id": self.fbid},
             "sender_action": typing_state
             })

        status = requests.post(self.post_message_url,
                               headers={"Content-Type": "application/json"},
                               data=response_msg)

        logger.debug('typing indicator status: {}'.format(status.text))

    def send_media(self, url, media_type, **kwargs):
        '''Send videos,gifs or url via fb messenger
        params: url : direct url to media source
                media_type : possible types are 'image', 'audio', 'video'.

        '''

        response_msg = dict(
            {"recipient": {"id": self.fbid},
             "message": {"attachment":
                         {'type': media_type,
                          'payload': {'url': url}
                          }
                         }
             })
        # add optional parameters to request
        response_msg.update(**kwargs)
        status = requests.post(self.post_message_url,
                               headers={"Content-Type": "application/json"},
                               data=json.dumps(response_msg))
        logger.debug(response_msg)
        logger.debug(
            'media sent of type {}: {}'.format(media_type, status.text))

    def send_template(self, *elements):
        '''
        send generic template
        params: *elements : dicts following generic template format
        '''
        post_message_url = 'https://graph.facebook.com/v2.6/me/messages?access_token={}'.format(
            self.token)
        payload_elems = [elem for elem in elements]
        response_msg = json.dumps(
            {"recipient": {"id": self.fbid},
             "message": {"attachment":
                         {'type': 'template',
                             'payload': {'template_type': 'generic',
                                         'elements': payload_elems,
                                         }
                          }
                         }
             })
        status = requests.post(post_message_url,
                               headers={"Content-Type": "application/json"},
                               data=response_msg)
        logger.debug('template sent to {}, status:'.format(self.fbid,
                                                           status.text))

    def _raw_send(self, data):
        post_message_url = 'https://graph.facebook.com/v2.6/me/messages?access_token={}'.format(
            self.token)

        status = requests.post(post_message_url,
                               headers={"Content-Type": "application/json"},
                               data=data)
        logger.debug(status.text)


class FbManage(FbMessenger):

    '''
    Object to manage user states such as activation,optout,stop and analytics
    '''

    def activate(self):
        '''
        set 'activated' field in database to True, if already activated
        then return False
        '''
        try:
            cond = db.FbUserInfo.objects(user_id=self.fbid).first().activated
        except AttributeError:
            # user does not exist
            self.get_userinfo()
            return True

        if not cond:
            logger.info('activating user: {}'.format(self.fbid))
            for user in db.FbUserInfo.objects(user_id=self.fbid):
                user.update(activated=True)
            return True
        else:
            logger.info('{} user is already activated'.format(self.fbid))
            return False

    def deactivate(self):
        ''' set 'activated' field in database to False '''
        for user in db.FbUserInfo.objects(user_id=self.fbid):
            user.update(activated=False)
        logger.info('user deactivated')
        self.say('I wish you luck in all your endeavours!')
        return True

    def optout(self):
        '''
        update user profile field to optout of data collection
        '''
        pass

    def stop(self):
        '''
        purge tasks queue and prompt for user data removal
        '''
        pass

    def get_userinfo(self):
        '''
        Retreive user information using fbid given in instance
        return a dict with fields: name
                                   timezone in Olson format
                                   gender
                                   userid
                                   optout - data collection optout
                                   activated - activation of tasks
        '''

        # check if user info existing in database
        # returns none if not found
        cond = next(db.FbUserInfo.objects(user_id=self.fbid), None)
        if cond:
            return cond
        else:
            get_message_url = '''https://graph.facebook.com/v2.6/{}?fields=first_name,last_name,profile_pic,locale,timezone,gender&access_token={}'''.format(
                self.fbid, self.token)
            req = requests.get(get_message_url)
            user_info = req.json()
            logger.debug(user_info)
            user_info['timezone'] = tz_mgmt.utc_to_tz(
                user_info['timezone'])

            user_info['user_id'] = self.fbid

            logger.info('New User Info Entry')
            entry = db.FbUserInfo(name=user_info['first_name'] + ' ' + user_info['last_name'],
                                  timezone=user_info['timezone'],
                                  gender=user_info['gender'],
                                  user_id=user_info['user_id'],
                                  activated=False)
            entry.save()
            return user_info


class FbHandler:

    '''
    class to sort facebook incoming webhooks and aggregate conversation
    context. This class assumes an entry is passed as json stringified
    '''

    def __init__(self, entry):
        logger.debug('FB - Handler')
        # determine type of entry and process
        if 'message' in entry:
            logger.info('rcvd message')
            self.rcvd_msg(entry)

        elif 'postback' in entry:
            logger.info('rcvd postback')
            self.postbacks(entry)
        elif 'read' in entry:
            logger.info('msg read')
            self.msg_seen(entry)

    def rcvd_msg(self, message):
        '''handle text messages'''
        if message['message'].get('payload') == 'null':
            # ignores quickreplies
            logger.info('null quickreply')
            pass
        if message['message'].get('payload') == 'begin':
            self.start(message['sender']['id'])
            logger.info('starting via payload')

        elif 'text' in message['message']:
            # humanize
            time.sleep(randint(0, 2))

            commands = ['ready', 'allons-y', 'vamos']
            txt = message['message']['text'].lower()
            cond = any([word in txt for word in commands])

            if cond:
                self.start(message['sender']['id'])
                logger.debug('start course')

            elif 'stop' in message['message']['text'].lower():
                bot = FbManage(message['sender']['id'])
                bot.deactivate()
                logger.info('user deactivated via text')

            elif 'meme' in message['message']['text'].lower():
                logger.debug('unknown command')
                bot = FbManage(message['sender']['id'])
                random_msg = choice(next(db.RandomMsg.objects()).texts)
                bot.send(random_msg)
            else:
                bot = FbManage(message['sender']['id'])
                bot.say('hmm?')
        else:
            bot = FbManage(message['sender']['id'])
            bot.say("I don't get it?")

    def msg_seen(self, status):
        '''handle seen notifications'''
        return None

    def postbacks(self, form):
        '''handle postback'''
        logger.debug('postback payload {}'.format(form['postback']['payload']))
        if form['postback']['payload'] == 'start':
            bot = FbManage(form['sender']['id'])
            logger.debug(
                'user getting started:{}'.format(bot.fbid))

            # How can we avoid hardcoding responses like these?
            quickreply = dict(content_type="text",
                              title="Let's Go!",
                              payload="begin"
                              )
            txt0 = 'Oh hello there! 😁'
            txt1 = ("Hey! My name’s Stanson and I’m here to help you get an A+"
                    " in Stanford course CS183B,‘How to Start a Startup’ by Sam Altman"
                    " a veritable who’s who of Silicon Valley heavy hitters.")
            txt2 = (" Get the courseware, answer the most important questions, and enjoy memes."
                    " Learning has never been this fun and easy."
                    )
            bot.say(txt0)
            time.sleep(2)
            bot.say(txt1)
            time.sleep(5)
            bot.say(txt2, quick_replies=[quickreply])
        elif form['postback']['payload'] == 'stop':
            bot = FbManage(form['sender']['id'])
            bot.deactivate()
            logger.info('user deactivated via postback')

    def start(self, fbid):
        bot = FbManage(fbid)
        logger.debug(
            'ready command from user:{}'.format(bot.fbid))

        # needs to check
        userinfo = bot.get_userinfo()

        if bot.activate():
            startupday0.delay(userinfo)
        else:
            logger.info('attempted activationg of activated bot')
            bot.say("Now why would you wanna register for a course twice?")


# Setup functions that compose objects for Celery to decorate
@celery_tasks.celeryapp.task
def send_msg(fbid, text, **kwargs):
    bot = FbMessenger(fbid)
    bot.send(text)


@celery_tasks.celeryapp.task
def send_msgs(fbid, msg_iter):
    # assign appropriate send function for types of msg
    # this function assumes a strucuture built in the models.py section

    #
    user_file = next(db.FbUserInfo.objects(user_id=fbid))
    for msg in msg_iter:
        # each msg is a dict
        # ignore scheduled messages, this is a temporary fix
        # not sustainable if user deactivates and immedietly activates,
        # duplicates occur
        if not user_file.activated:
            logger.info('caught deactivated user!')
            pass
        else:
            bot = FbMessenger(fbid)
            if msg.get('elems'):
                elems = msg['elems']
                msg.pop('elems')
                # pass optional params
                bot.send_template(*elems, **msg)

            if msg.get('text'):
                text = msg['text']
                msg.pop('text')
                bot.say(text, True, **msg)
            if msg.get('url'):
                url = msg['url']
                msg.pop('url')
                bot.send(url, True, **msg)
            time.sleep(randint(3, 7))


@celery_tasks.celeryapp.task
def FbHandle(payload):
    '''Handle facebook messenger asyncronously using Celery decorator'''
    time.sleep(3)
    FbHandler(payload)


hour_tdelta = timedelta(seconds=10)
day_tdelta = timedelta(minutes=2)


@celery_tasks.celeryapp.task
def startupday0(userinfo):
    events = next(db.FbMsgrTexts.objects(day=0)).events
    eta = datetime.now(timezone(userinfo['timezone']))
    for evnt in events:
        # the idea is to async schedule events through out the day
        send_msgs.apply_async(args=[userinfo['user_id'], evnt['msgs']],
                              countdown=1)

    # schedule monday class at around 10
    #future = tz_mgmt.find_day(eta, 0).replace(hour=9, minute=50 + randint(5, 9))
    future = eta + day_tdelta
    logger.info('Scheduled day1 for {}'.format(future.isoformat()))
    # check if user wants to stop notifications
    user_file = next(db.FbUserInfo.objects(user_id=userinfo['user_id']))

    if user_file.activated:
        #startupday1.apply_async(args=[userinfo], eta=future)
        copy_ver = iter([item for item in db.FbMsgrTexts.objects])
        recurse.apply_async(args=[copy_ver, userinfo], countdown=5)
    else:
        logger.info('did not schedule for deactivaed usr {}'.format(
                    userinfo['user_id']))


@celery_tasks.celeryapp.task
def recurse(fb_obj, userinfo):
    ''' recursevly calls itself to iterate through all documents
    type FbMsgrTexts (contains text/media to send) in the NoSql database.
    At the end it will signal that the iteration is done by changing
    'activated' field of a user in FbUserInfo
    '''
    try:
        doc = next(fb_obj)
    except StopIteration:
        logger.info('days are done')
        user = next(db.FbUserInfo.objects(user_id=userinfo['user_id']))
        user.activated = False
    else:
        user = next(db.FbUserInfo.objects(user_id=userinfo['user_id']))
        now = datetime.now(timezone(userinfo['timezone']))
        for evnt in doc.events:
            # the idea is to async schedule events through out the day
            send_msgs.apply_async(args=[userinfo['user_id'], evnt['msgs']],
                                  eta=now + hour_tdelta)
        if user.activated:
            logger.info(user.activated)
            recurse.apply_async(args=[fb_obj, userinfo], eta=now + day_tdelta)
        else:
            logger.debug('caught de activated users')
