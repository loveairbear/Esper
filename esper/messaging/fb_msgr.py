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
        logger.info("text message sent: {}".format(status.text))

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
            cond = db.FbUserInfo.objects(fb_id=self.fbid).first().activated
        except AttributeError:
            # user does not exist
            self.get_userinfo()
            return True

        if not cond:
            logger.info('activating user: {}'.format(self.fbid))
            for user in db.FbUserInfo.objects(fb_id=self.fbid):
                user.update(activated=True)
            return True
        else:
            logger.info('{} user is already activated'.format(self.fbid))
            return False

    def deactivate(self):
        ''' set 'activated' field in database to False '''
        for user in db.FbUserInfo.objects(fb_id=self.fbid):
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
        cond = next(db.FbUserInfo.objects(fb_id=self.fbid), None)
        if cond:
            return cond
        else:
            get_message_url = 'https://graph.facebook.com/v2.6/{}?fields=first_name,last_name,profile_pic,locale,timezone,gender&access_token={}'.format(
                self.fbid, self.token)
            req = requests.get(get_message_url)
            user_info = req.json()
            logger.debug(user_info)
            user_info['timezone'] = tz_mgmt.utc_to_tz(
                user_info['timezone'])

            user_info['fb_id'] = self.fbid

            logger.info('New User Info Entry')
            entry = db.FbUserInfo(name=user_info['first_name'] + ' ' + user_info['last_name'],
                                  timezone=user_info['timezone'],
                                  gender=user_info['gender'],
                                  fb_id=user_info['fb_id'],
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
            time.sleep(2)
            self.rcvd_msg(entry)

        elif 'postback' in entry:
            logger.info('rcvd postback')
            time.sleep(2)
            self.postbacks(entry)
        elif 'read' in entry:
            logger.info('msg read')
            self.msg_seen(entry)

    def rcvd_msg(self, message):
        '''handle text messages'''
        reply = message['message'].get('quick_reply')
        if reply:
            payload = reply.get('payload')
            if payload == 'null':
                # ignores quickreplies
                logger.info('null quickreply')
                pass
            if payload == 'begin':
                self.start(message['sender']['id'])
                logger.info('starting via payload')
            if payload:
                if payload.startswith('$'):
                    # echo back payload
                    # this is a duct tape solution to acting like a conversation
                    bot = FbManage(message['sender']['id'])
                    bot.send(payload[1:])

        elif 'text' in message['message']:
            commands = ['ready', 'allons-y', 'vamos']
            txt = message['message']['text'].lower()
            cond = any([word in txt for word in commands])

            if cond:
                self.start(message['sender']['id'])
                logger.info('start course')

            elif 'stop' in txt:
                bot = FbManage(message['sender']['id'])
                bot.deactivate()
                logger.info('user deactivated via text')

            elif self.keywords(message):
                pass
            else:
                rand_msgs = db.RandomMsg.objects(keywords='random')[0]
                msg = choice(rand_msgs['texts'])
                send_msg(message['sender']['id'], msg)
                # change this to suggest keywords
        else:
            bot = FbManage(message['sender']['id'])
            bot.say("I don't get it?")

    def keywords(self, msg):
        ''' check if any keywords from a database document matches the msg,
        then randomly select a message from that document to send back
        '''
        rand_msgs = db.RandomMsg.objects()
        txt = msg['message']['text'].lower()
        for doc in rand_msgs:
            checks = [keyw in txt for keyw in doc.keywords]
            if any(checks):
                random_msg = choice(doc.texts)
                send_msg(msg['sender']['id'], random_msg)
                return True
        return False

    def msg_seen(self, status):
        '''handle seen notifications'''
        return None

    def postbacks(self, form):
        '''handle postback'''
        logger.debug('postback payload {}'.format(form['postback']['payload']))
        if form['postback']['payload'] == 'start':
            bot = FbManage(form['sender']['id'])
            logger.info(
                'user getting started:{}'.format(bot.fbid))

            # How can we avoid hardcoding responses like these?
            quickreply = dict(content_type="text",
                              title="Let's Go!",
                              payload="begin"
                              )
            txt0 = 'Oh hello there! 🐢'
            txt1 = ("My name’s Stanson and I’m here to help you get an A+ in Stanford course CS183B, ‘How to Start a Startup’. 🎓")
            txt2 = ("It’s by Y-Combinator and features a veritable who’s who of Silicon Valley heavy hitters.🔥💯🔑"
                    )

            bot.say(txt0)
            time.sleep(3)
            bot.say(txt1)
            time.sleep(5)
            bot.say(txt2, quick_replies=[quickreply])
        elif form['postback']['payload'] == 'stop':
            bot = FbManage(form['sender']['id'])
            bot.deactivate()
            logger.info('user deactivated via postback')

    def start(self, fbid):
        ''' start the main program iterating through the days '''
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
def send_msg(fbid, msg, **kwargs):
    bot = FbMessenger(fbid)
    if msg.get('elems'):
            elems = msg['elems']
            msg.pop('elems')
            # pass optional params
            bot.send_template(*elems, **msg)
            logger.debug('sending template')
    elif msg.get('text'):
            text = msg['text']
            msg.pop('text')
            bot.say(text, True, **msg)
            logger.debug('sending text')
    elif msg.get('url'):
            url = msg['url']
            msg.pop('url')
            bot.send(url, True, **msg)
            logger.debug('sending media')


@celery_tasks.celeryapp.task
def send_msgs(fbid, msg_iter):
    ''' given a user if and a msg iterator, send them all consecutively'''
    # assign appropriate send function for types of msg
    # this function assumes a strucuture built in the models.py section
    user_file = next(db.FbUserInfo.objects(fb_id=fbid))
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
            try:
                tmp = msg.pop('pause')
            except KeyError:
                tmp = None
            if msg.get('elems'):
                elems = msg['elems']
                msg.pop('elems')
                # pass optional params
                bot.send_template(*elems, **msg)
                logger.debug('sending template')
            elif msg.get('text'):
                text = msg['text']
                msg.pop('text')
                bot.say(text, True, **msg)
                logger.debug('sending text')
            elif msg.get('url'):
                url = msg['url']
                msg.pop('url')
                bot.send(url, True, **msg)
                logger.debug('sending media')
            if tmp:
                # break convo
                logger.info('pausing')
                send_msgs.apply_async(args=[fbid, msg_iter],
                                      countdown=int(tmp))
                # break operation
                return None
            # take a breath before starting next sentence
            time.sleep(randint(1, 3))


@celery_tasks.celeryapp.task
def FbHandle(payload):
    '''Handle facebook messenger asyncronously using Celery decorator'''
    FbHandler(payload)


hour_tdelta = timedelta(hours=4)
day_tdelta = timedelta(days=1)


@celery_tasks.celeryapp.task
def startupday0(userinfo):
    copy_ver = iter([item for item in db.FbMsgrTexts.objects])
    events = next(copy_ver).events
    eta = datetime.now(timezone(userinfo['timezone']))
    send_msgs.delay(userinfo['fb_id'], events[0]['msgs'])
    for evnt in events[1:]:
        # the idea is to async schedule events through out the day
        send_msgs.apply_async(args=[userinfo['fb_id'], evnt['msgs']],
                            eta=eta + hour_tdelta)
    # schedule monday class at around 10
    future = tz_mgmt.find_day(eta, 0).replace(hour=9, minute=50 + randint(5, 9))
    
    # future = eta + day_tdelta
    # check if user wants to stop notifications
    user_file = next(db.FbUserInfo.objects(fb_id=userinfo['fb_id']))

    if user_file.activated:
        recurse.apply_async(args=[copy_ver, userinfo], countdown=1)
    else:
        logger.info('did not schedule for deactivaed usr {}'.format(
                    userinfo['fb_id']))


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
        user = next(db.FbUserInfo.objects(fb_id=userinfo['fb_id']))
        user.activated = False
    else:
        user = next(db.FbUserInfo.objects(fb_id=userinfo['fb_id']))
        now = datetime.now(timezone(userinfo['timezone']))


        send_msgs.delay(userinfo['fb_id'], doc.events[0]['msgs'])
        for evnt in doc.events[1:]:
            # the idea is to async schedule events through out the day
            send_msgs.apply_async(args=[userinfo['fb_id'], evnt['msgs']],
                                  eta=now + hour_tdelta)
        if user.activated:
            # avoid weekends
            recurse.apply_async(args=[fb_obj, userinfo],
                                eta=tz_mgmt.not_weekend(now + day_tdelta))
        else:
            logger.debug('caught activated user')
