import json
import requests
from os import environ
import logging
import time
from random import randint, choice
from datetime import datetime, timedelta
from pytz import timezone


from kin.database import models as db
from kin.scheduling import timezone_manage, celery_tasks

logging.basicConfig()
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
        post_message_url = 'https://graph.facebook.com/v2.6/me/messages?access_token={}'.format(
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
        logger.debug('media sent of type {}: {}'.format(media_type, status.text))

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
            logger.debug('activating user: {}'.format(self.fbid))
            for user in db.FbUserInfo.objects(user_id=self.fbid):
                user.update(activated=True)
            return True
        else:
            logger.debug('{} user is already activated'.format(self.fbid))
            return False

    def deactivate(self):
        ''' set 'activated' field in database to False '''
        for user in db.FbUserInfo.objects(user_id=self.fbid):
            user.update(activated=False)
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
        '''

        # check if user info existing in database

        cond = str(self.fbid) in [doc.user_id for doc in db.FbUserInfo.objects(user_id=self.fbid)]
        if cond:
            return(next(db.FbUserInfo.objects(user_id=self.fbid), None))
        else:
            get_message_url = '''https://graph.facebook.com/v2.6/{}?fields=first_name,last_name,profile_pic,locale,timezone,gender&access_token={}'''.format(
                self.fbid, self.token)
            req = requests.get(get_message_url)
            user_info = req.json()
            logger.debug(user_info)
            user_info['timezone'] = timezone_manage.utc_to_tz(
                user_info['timezone'])

            user_info['user_id'] = self.fbid

            logger.info('New User Info Entry')
            entry = db.FbUserInfo(name=user_info['first_name'] + ' ' + user_info['last_name'],
                               timezone=user_info['timezone'],
                               gender=user_info['gender'],
                               user_id=user_info['user_id'],
                               activated=False)
            entry.save()
            # set typing indicator on
            self._typing_indicate('typing_on')

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
            logger.debug('rcvd message')
            self.rcvd_msg(entry)

        elif 'postback' in entry:
            logger.debug('rcvd postback')
            self.postbacks(entry)
        elif 'read' in entry:
            logger.debug('msg read')
            self.msg_seen(entry)

    def rcvd_msg(self, message):
        '''handle text messages'''
        if 'text' in message['message']:
            # humanize
            time.sleep(randint(1, 5))
            commands = ["let's go!", 'ready', 'go!']
            txt = message['message']['text'].lower()
            cond = any([word in txt for word in commands])
            if cond:
                bot = FbManage(message['sender']['id'])
                logger.debug(
                    'ready command from user:{}'.format(bot.fbid))

                # needs to check
                userinfo = bot.get_userinfo()

                if bot.activate():
                    startupday0.delay(userinfo)
                else:
                    bot.say('already activated')
            else:
                logger.debug('unknown command')
                bot = FbManage(message['sender']['id'])
                random_msg = choice(next(db.RandomMsg.objects()).texts)
                bot.send(random_msg)
        elif 'metadata' in message['message']:
            logger.debug('Got Metadata')
            bot = FbManage(message['sender']['id'])
            bot.say('umm')
        else:
            bot = FbManage(message['sender']['id'])
            bot.say('Hmm?')

    def msg_seen(self, status):
        '''handle seen notifications'''

        pass

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
                                  payload="doesntmatter"
                                  )
                txt1 = ("Hey! My name’s Stanson and I’m here to help you get an A+"
                       " in Stanford course CS183B,‘How to Start a Startup’ by Sam Altman"
                       " a veritable who’s who of Silicon Valley heavy hitters.")
                txt = (" Get the courseware, answer the most important questions, and enjoy memes."
                       " Learning has never been this fun and easy."
                       )
                bot.say(txt1)
                time.sleep(5)
                bot.say(txt, quick_replies=[quickreply])

                



# Setup functions that compose objects for Celery to decorate
@celery_tasks.celeryapp.task
def send_msg(fbid, text, **kwargs):
    bot = FbMessenger(fbid)
    bot.send(text)


@celery_tasks.celeryapp.task
def send_msgs(fbid, msg_iter):
    bot = FbMessenger(fbid)
    # assign appropriate send function for types of msg
    # this function assumes a strucuture built in the models.py section
    for msg in msg_iter:
        # each msg is a dict
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
        time.sleep(5)


@celery_tasks.celeryapp.task
def FbHandle(payload):
    '''Handle facebook messenger asyncronously using Celery decorator'''
    FbHandler(payload)



hour_tdelta = timedelta(seconds=10)
day_tdelta = timedelta(minutes=1)
##### Hardcoded Days for StartUp Bot
@celery_tasks.celeryapp.task
def startupday0(userinfo):
    bot = FbMessenger(userinfo['user_id'])
    events = next(db.FbMsgrTexts.objects(day=0)).events
    for evnt in events:
        # the idea is to aync schedule events through out the day
        send_msgs.apply_async(args=[userinfo['user_id'], evnt['msgs']],countdown=5)


    eta = datetime.now(timezone(userinfo['timezone']))
    #future = eta.replace(day=eta.day + 1, hour=12, minute=0)
    future = eta + day_tdelta
    startupday1.apply_async(args=[userinfo], eta=future)


@celery_tasks.celeryapp.task
def startupday1(userinfo):
    logger.debug('startupday1')
    events = next(db.FbMsgrTexts.objects(day=1)).events
    eta = datetime.now(timezone(userinfo['timezone']))
    for evnt in events:
        # the idea is to aync schedule events through out the day
        send_msgs.apply_async(args=[userinfo['user_id'], evnt['msgs']],
                              eta=eta + hour_tdelta)

    #future = eta.replace(day=eta.day + 1, hour=12, minute=0)
    future = eta + day_tdelta
    startupday2.apply_async(args=[userinfo], eta=future)


@celery_tasks.celeryapp.task
def startupday2(userinfo):
    events = next(db.FbMsgrTexts.objects(day=2)).events
    eta = datetime.now(timezone(userinfo['timezone']))
    for evnt in events:
        # the idea is to aync schedule events through out the day
        send_msgs.apply_async(args=[userinfo['user_id'], evnt['msgs']],
                              eta=eta + hour_tdelta)
    
    eta += day_tdelta

    startupday3.apply_async(args=[userinfo], eta=eta)


@celery_tasks.celeryapp.task
def startupday3(userinfo):
    events = next(db.FbMsgrTexts.objects(day=3)).events
    eta = datetime.now(timezone(userinfo['timezone']))
    for evnt in events:
        # the idea is to aync schedule events through out the day
        send_msgs.apply_async(args=[userinfo['user_id'], evnt['msgs']],
                              eta=eta + hour_tdelta)
    
    eta += day_tdelta
    startupday4.apply_async(args=[userinfo], eta=eta)



@celery_tasks.celeryapp.task
def startupday4(userinfo):
    events = next(db.FbMsgrTexts.objects(day=4)).events
    eta = datetime.now(timezone(userinfo['timezone']))
    for evnt in events:
        # the idea is to aync schedule events through out the day
        send_msgs.apply_async(args=[userinfo['user_id'], evnt['msgs']],
                              eta=eta + hour_tdelta)
    
    eta += day_tdelta
    startupday5.apply_async(args=[userinfo], eta=eta)


@celery_tasks.celeryapp.task
def startupday5(userinfo):
    events = next(db.FbMsgrTexts.objects(day=5)).events
    eta = datetime.now(timezone(userinfo['timezone']))
    for evnt in events:
        # the idea is to aync schedule events through out the day
        send_msgs.apply_async(args=[userinfo['user_id'], evnt['msgs']],
                              eta=eta + hour_tdelta)
    
    eta += day_tdelta
    startupday6.apply_async(args=[userinfo], eta=eta)


@celery_tasks.celeryapp.task
def startupday6(userinfo):
    events = next(db.FbMsgrTexts.objects(day=6)).events
    eta = datetime.now(timezone(userinfo['timezone']))
    for evnt in events:
        # the idea is to aync schedule events through out the day
        send_msgs.apply_async(args=[userinfo['user_id'], evnt['msgs']],
                              eta=eta + hour_tdelta)
    
    eta += day_tdelta
    startupday7.apply_async(args=[userinfo], eta=eta)


@celery_tasks.celeryapp.task
def startupday7(userinfo):
    events = next(db.FbMsgrTexts.objects(day=7)).events
    eta = datetime.now(timezone(userinfo['timezone']))
    for evnt in events:
        # the idea is to aync schedule events through out the day
        send_msgs.apply_async(args=[userinfo['user_id'], evnt['msgs']],
                              eta=eta + hour_tdelta)
    
    eta += day_tdelta
    startupday8.apply_async(args=[userinfo], eta=eta)


@celery_tasks.celeryapp.task
def startupday8(userinfo):
    events = next(db.FbMsgrTexts.objects(day=8)).events
    eta = datetime.now(timezone(userinfo['timezone']))
    for evnt in events:
        # the idea is to aync schedule events through out the day
        send_msgs.apply_async(args=[userinfo['user_id'], evnt['msgs']],
                              eta=eta + hour_tdelta)
    
    eta += day_tdelta
    startupday9.apply_async(args=[userinfo], eta=eta)


@celery_tasks.celeryapp.task
def startupday9(userinfo):
    events = next(db.FbMsgrTexts.objects(day=9)).events
    eta = datetime.now(timezone(userinfo['timezone']))
    for evnt in events:
        # the idea is to aync schedule events through out the day
        send_msgs.apply_async(args=[userinfo['user_id'], evnt['msgs']],
                              eta=eta + hour_tdelta)
    eta += day_tdelta
    startupday10.apply_async(args=[userinfo], eta=eta)
    
@celery_tasks.celeryapp.task
def startupday10(userinfo):
    bot = FbManage(userinfo['user_id'])
    events = next(db.FbMsgrTexts.objects(day=10)).events
    eta = datetime.now(timezone(userinfo['timezone']))
    for evnt in events:
        # the idea is to aync schedule events through out the day
        send_msgs.apply_async(args=[userinfo['user_id'], evnt['msgs']],
                              eta=eta + hour_tdelta)
    bot.deactivate()



if __name__ == '__main__':
    # remove dis

    b = dict(title='title', item_url='http://tex.stackexchange.com/questions/173317/is-there-a-latex-wrapper-for-use-in-google-docs',
             image_url='https://s-media-cache-ak0.pinimg.com/736x/1d/50/94/1d5094b488985c34557942d6867e67e3.jpg')

    c = dict(title='title1', item_url='https://www.google.ca/',
             image_url='https://m1.behance.net/rendition/modules/40023737/disp/8aaaa64130c793e25ff9dc48dad3a8a1.jpg')

    a.send_template(b, c)
    # a.send('https://m1.behance.net/rendition/modules/40023737/disp/8aaaa64130c793e25ff9dc48dad3a8a1.jpg')
