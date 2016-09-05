import json
import requests
from os import environ
import logging
import time
from random import randint, choice
from datetime import datetime, timedelta
from pytz import timezone
from uuid import uuid4


from esper.database import models as db
from esper.scheduling import tz_mgmt, celery_tasks


logger = logging.getLogger(__name__)


class FbMessenger:

    '''
    FbMessenger simplified interface to send messages
    '''

    def __init__(self, fbid=None, userinfo=None,
                 session=None, token=environ.get('FB_TOKEN')):
        self.token = token
        self.fbid = fbid
        self.user = userinfo
        self.post_message_url = 'https://graph.facebook.com/v2.6/me/messages?access_token={}'.format(
            self.token)
        self.session = session
        #self._typing_indicate('typing_on')

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

        vid_sfix = ['.mp4', '.gifv', '.webm']
        vid_cond = any([sfix in payload for sfix in vid_sfix])

        if img_cond and cond:
            self.send_media(payload, 'image', **kwargs)
        elif vid_cond and cond:
            self.send_media(payload, 'video', **kwargs)
        elif '.mp3' in payload and cond:
            self.send_media(payload, 'audio', **kwargs)
        else:
            # send a normal text
            self.say(payload, **kwargs)

    def say(self, text, **kwargs):
        '''
        send a text message to the user defined in FbMessenger object
        params: text: message to send,
                delay: randomized delay times after messages
                **kwargs: quickreplies, metadata, etc...

        '''
        response_msg = ({"recipient": {"id": self.fbid},
             "message": {"text": text}
             })

        # append optional parameters to post form such as quick replies
        response_msg['message'].update(**kwargs)
        status = self._raw_send(response_msg)
        logger.info("text message sent: {}".format(status.text))
        return status

    def _typing_indicate(self):
        response_msg = (
            {"recipient": {"id": self.fbid},
             "sender_action": 'typing_on'
             })
        status = self._raw_send(response_msg)

        logger.debug('typing indicator status: {}'.format(status.text))
        return status

    def send_media(self, url, media_type, **kwargs):
        '''Send videos,gifs or url via fb messenger
        params: url : direct url to media source
                media_type : possible types are 'image', 'audio', 'video'.

        '''

        response_msg = ({"recipient": {"id": self.fbid},
             "message": {"attachment":
                         {'type': media_type,
                          'payload': {'url': url}
                          }
                         }
             })
        # add optional parameters to request
        response_msg.update(**kwargs)
        status = self._raw_send(response_msg)
        logger.info(
            'media sent of type {}: {}'.format(media_type, status.text))
        return status

    def send_template(self, *elements):
        '''
        send generic template
        params: *elements : dicts following generic template format
        '''
        payload_elems = [elem for elem in elements]
        response_msg = ({"recipient": {"id": self.fbid},
             "message": {"attachment":
                         {'type': 'template',
                             'payload': {'template_type': 'generic',
                                         'elements': payload_elems,
                                         }
                          }
                         }
             })
        status = self._raw_send(response_msg)
        logger.info('template sent to {}, status:'.format(self.fbid,
                                                           status.text))
        return status

    def send_button(self, text, *elems):
        buttons = [button for button in elems]
        response_msg = {
            "recipient": {
                "id": self.fbid
            },
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "button",
                        "text": text,
                        "buttons": buttons
                    }
                }
            }
        }
        return self._raw_send(response_msg)
    def _raw_send(self, data):
        post_message_url = 'https://graph.facebook.com/v2.6/me/messages?access_token={}'.format(
            self.token)
        if self.session:
            status = self.session.post(post_message_url,
                               headers={"Content-Type": "application/json"},
                               data=json.dumps(data))
        else:
            status = requests.post(post_message_url,
                               headers={"Content-Type": "application/json"},
                               data=json.dumps(data))
        return status


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
            cond = db.FbUserInfo.objects.get(fb_id=self.fbid).activated
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
            tasks = user.tasks
            celery_tasks.celeryapp.control.revoke(tasks)

        logger.info('user deactivated')
        self.say('I wish you luck in all your endeavours!')
        return True
    def start(self):
        logger.debug(
            'ready command from user:{}'.format(self.fbid))

        # needs to check
        userinfo = self.get_userinfo()

        if self.activate():
            startupday0.delay(userinfo)
        else:
            logger.info('attempted activation of activated bot')
            self.say("Now why would you wanna register for a course twice?")
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
        try:
            cond = db.FbUserInfo.objects.get(fb_id=self.fbid)
        except db.mdb.errors.DoesNotExist:
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
                                  activated=False,
                                  account=uuid4().hex)
            entry.save()
            return user_info
        else:
            return cond

class TextProc:
    ''' sessions is a keep alive session from requests lib
    '''
    def __init__(self, entry, session=None):
        if self.quick_payload(entry):
            pass
        elif self.text_msg(entry):
            pass
    def quick_payload(self,message):
        reply = message['message'].get('quick_reply')
        if reply:
            payload = reply.get('payload')
            if payload == 'null':
                # ignores quickreplies
                logger.info('null quickreply')
                pass
            if payload == 'start':
                bot = FbManage(message['sender']['id'])
                bot.start()
                logger.info('starting via payload')
            if payload.startswith('$'):
                bot = FbMessenger(message['sender']['id'])
                # echo back payload
                # this is a duct tape solution to acting like a
                # conversation
                bot.send(payload[1:])
            else:
                self.keywords(message)
            return True
        else:
            return False
    def text_msg(self,message):
        if 'text' in message['message']:
            commands = ['ready', 'allons-y', 'vamos']
            txt = message['message']['text'].lower()
            cond = any([word in txt for word in commands])
            if cond:
                bot = FbManage(message['sender']['id'])
                bot.start()
                logger.info('start course')

            elif 'stop' in txt:
                bot = FbManage(message['sender']['id'])
                bot.deactivate()
                logger.info('user deactivated via text')

            elif self.keywords(message):
                # found keywords, now doing stuff
                pass
            else:
                rand_msgs = db.RandomMsg.objects.get(keywords='random')
                msg = choice(rand_msgs['texts'])
                send_msg(message['sender']['id'], msg)
            return True
        else:
            return False
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
class PostBackProc:
    def __init__(self, entry, session=None):
        logger.debug('postback payload {}'.format(entry['postback']['payload']))
        if entry['postback']['payload'] == 'intro':
            bot = FbManage(entry['sender']['id'])
            logger.info(
                'user getting started:{}'.format(bot.fbid))

            # How can we avoid hardcoding responses like these?
            quickreply = dict(content_type="text",
                              title="Let's Go!",
                              payload="start"
                              )
            txt0 = 'Oh hello there! 🐢'
            txt1 = (
                "My name’s Stanson and I’m here to help you get an A+ in Stanford course CS183B, ‘How to Start a Startup’. 🎓")
            txt2 = ("It’s by Y-Combinator and features a veritable who’s who of Silicon Valley heavy hitters.🔥💯🔑"
                    )

            bot.say(txt0)
            bot._typing_indicate('typing_on')
            time.sleep(1)
            bot.say(txt1)
            bot._typing_indicate('typing_on')
            time.sleep(2)
            bot.say(txt2, quick_replies=[quickreply])
        if entry['postback']['payload'] == 'start':
            bot = FbManage(entry['sender']['id'])
            bot.start()
        elif entry['postback']['payload'] == 'stop':
            bot = FbManage(entry['sender']['id'])
            bot.deactivate()
            logger.info('user deactivated via postback')
        elif entry['postback']['payload'].startswith('$'):
            logger.info('got echo: {}'.format(entry['postback']['payload'][1:]))
            bot = FbMessenger(entry['sender']['id'])
            bot.say(entry['postback']['payload'][1:])
        elif entry['postback']['payload'] == 'null':
            pass

class MsgSeen:
    def __init__(self, entry, session=None):
        pass
 



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
    elif msg.get('buttons'):
        bot.send_button(msg.get('text'),
                        *msg.get('buttons'))
        logger.info('sending buttons')
    elif msg.get('text'):
        text = msg['text']
        msg.pop('text')
        bot.say(text, **msg)
        logger.debug('sending text')
    elif msg.get('url'):
        url = msg['url']
        msg.pop('url')
        bot.send(url, **msg)
        logger.debug('sending media')


@celery_tasks.celeryapp.task(ignore_result=False)
def send_msgs(fbid, msg_iter):
    ''' given a user if and a msg iterator, send them all consecutively'''
    # assign appropriate send function for types of msg
    # this function assumes a strucuture built in the models.py section
    try:
        user_file = db.FbUserInfo.objects.get(fb_id=fbid)
        for msg in msg_iter:
            # each msg is a dict
            # ignore scheduled messages, this is a temporary fix
            # not sustainable if user deactivates and immedietly activates,
            # duplicates occur
            if not user_file.activated:
                logger.info('caught deactivated user!')
                pass
            else:
                try:
                    tmp = msg.pop('pause')
                except KeyError:
                    tmp = None
    
                send_msg(fbid, msg)
                if tmp:
                    # break convo
                    logger.info('pausing')
                    send_msgs.apply_async(args=[fbid, msg_iter],
                                          countdown=int(tmp))
                    # break operation
                    return None
    except db.mdb.errors.DoesNotExist:
        return None



@celery_tasks.celeryapp.task(ignore_result=False)
def process_text(payload, session):
    '''Handle facebook messenger asyncronously using Celery decorator'''
    db.mdb.connect('database', host=environ.get('MONGODB_URI'))
    TextProc(payload, session)


@celery_tasks.celeryapp.task(ignore_result=False)
def process_postback(payload, session):
    '''Handle facebook messenger asyncronously using Celery decorator'''
    db.mdb.connect('database', host=environ.get('MONGODB_URI'))
    PostBackProc(payload, session)


@celery_tasks.celeryapp.task(ignore_result=False)
def process_msg_read(payload, session):
    '''Handle facebook messenger asyncronously using Celery decorator'''
    # db.mdb.connect('database', host=environ.get('MONGODB_URI'))
    # PostBackProc(payload, session)
    pass
    


hour_tdelta = timedelta(hours=4)
day_tdelta = timedelta(days=1)


@celery_tasks.celeryapp.task(ignore_result=False)
def startupday0(userinfo):
    db.mdb.connect('database', host=environ.get('MONGODB_URI'))
    logger.info([item.day for item in db.FbMsgrTexts.objects().order_by('day')])
    copy_ver = iter([item for item in db.FbMsgrTexts.objects().order_by('day')])
    events = next(copy_ver).events
    eta = datetime.now(timezone(userinfo['timezone']))
    send_msgs.delay(userinfo['fb_id'], events[0]['msgs'])
    for evnt in events[1:]:
        # the idea is to async schedule events through out the day
        send_msgs.apply_async(args=[userinfo['fb_id'], evnt['msgs']],
                              eta=eta + hour_tdelta)
    # schedule monday class at around 10
    future = tz_mgmt.find_day(eta, 0).replace(
        hour=9, minute=50 + randint(5, 9))

    # future = eta + day_tdelta
    # check if user wants to stop notifications
    user_file = db.FbUserInfo.objects.get(fb_id=userinfo['fb_id'])

    if user_file.activated:
        task = recurse.apply_async(args=[copy_ver, userinfo], eta=future)
        user_file.tasks.append(task)
    else:
        logger.info('did not schedule for deactivaed usr {}'.format(
                    userinfo['fb_id']))


@celery_tasks.celeryapp.task(ignore_result=False)
def recurse(fb_obj, userinfo):

    ''' recursevly calls itself to iterate through all documents
    type FbMsgrTexts (contains text/media to send) in the NoSql database.
    At the end it will signal that the iteration is done by changing
    'activated' field of a user in FbUserInfo
    '''
    db.mdb.connect('database', host=environ.get('MONGODB_URI'))
    try:
        doc = next(fb_obj)
    except StopIteration:
        logger.info('days are done')
        user = next(db.FbUserInfo.objects(fb_id=userinfo['fb_id']))
        user.activated = False
    else:
        user = next(db.FbUserInfo.objects(fb_id=userinfo['fb_id']))
        

        # remove consumed task id from db
        user.tasks.remove(recurse.request.id)
        now = datetime.now(timezone(userinfo['timezone']))
        if user.activated:
            send_msgs.delay(userinfo['fb_id'], doc.events[0]['msgs'])
            for evnt in doc.events[1:]:
                # the idea is to async schedule events through out the day
                send_msgs.apply_async(args=[userinfo['fb_id'], evnt['msgs']],
                                  eta=now + hour_tdelta)
            # avoid weekends
            task = recurse.apply_async(args=[fb_obj, userinfo],
                               eta=tz_mgmt.not_weekend(now + day_tdelta))
            # put scheduled task id into db
            user.tasks.append(task.task_id)
            
        else:
            logger.debug('caught activated user')
