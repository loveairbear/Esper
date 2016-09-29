
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
from esper.messaging import core

logger = logging.getLogger(__name__)


class FbMessenger:
    """FbMessenger simplified interface to send messages."""

    def __init__(self, fbid=None, userinfo=None,
                 session=None, token=environ.get('FB_TOKEN')):
        self.token = token
        self.fbid = fbid
        self.user = userinfo
        self.post_message_url = 'https://graph.facebook.com/v2.6/me/messages?access_token={}'.format(
            self.token)
        self.session = session

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
        logger.debug("text message sent: {}".format(status.text))
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
                                      'payload': {'url': url,
                                                  "is_reusable": True}
                                     }
                                    }
                         })
        # add optional parameters to request
        response_msg.update(**kwargs)
        status = self._raw_send(response_msg)
        logger.debug(
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
        logger.debug('template sent to {}, status:'.format(self.fbid,
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
                                       headers={
                                           "Content-Type": "application/json"},
                                       data=core.json.dumps(data))
        else:
            status = requests.post(post_message_url,
                                   headers={
                                       "Content-Type": "application/json"},
                                   data=core.json.dumps(data))
        core.track_out(data, status.text)
        if status.text.get('error'):
            raise ValueError(status.text['error']['message'])
        return status


class FbManage(FbMessenger):
    """Object to manage user states such as activation,optout,stop and analytics."""

    def activate(self):
        """
        Set 'activated' field in database to True, if already activated
        then return False.
        """

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
            logger.warning('deleting tasks: {}'.format(tasks))
            celery_tasks.celeryapp.control.revoke(tasks)
        user.tasks = []
        user.save()
        self.say('Say "ready" whenever you want to start again 🤘 ')
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
            self.say(
                "You're already registered! Type 'menu' for more options")

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
    """Sessions is a keep alive session from requests lib."""

    def __init__(self, entry, session=None):
        if self.quick_payload(entry):
            pass
        elif self.text_msg(entry):
            pass

    def quick_payload(self, message):
        reply = message['message'].get('quick_reply')
        if reply:
            payload = reply.get('payload')
            if payload == 'null':
                # ignores quickreplies
                logger.info('null quickreply')
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
            if payload.startswith('#dev_'):
                bot = FbManage(message['sender']['id'])
                param = payload[5:]
                userinfo = bot.get_userinfo()
                now = datetime.now(timezone(userinfo['timezone']))
                user_file = db.FbUserInfo.objects().get(fb_id=bot.fbid)
                # day 0 is consumed as soon as event is triggered
                days = len(db.FbMsgrTexts.objects()) - 1
                copy_ver = iter(range(1, days))
                logger.warning(copy_ver)
                if param == "tomorrow":
                    bot.say("im excited! i'll talk to you tomorrow")
                    future = now.replace(day=now.day + 1, hour=9,
                                         minute=50 + randint(5, 9))

                elif param == "monday":
                    bot.say("great! i'll see ya in class on monday")
                    future = tz_mgmt.find_day(now, 0).replace(
                        hour=9, minute=50 + randint(5, 9))
                # elif param == "later": snooze content
                task = recurse.apply_async(args=[copy_ver, userinfo],
                                           eta=future)
                user_file.tasks = user_file.tasks + [task.task_id]
                user_file.save()
            else:
                self.keywords(message)
            return True
        else:
            return False

    def text_msg(self, message):
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
            checks = [keyw == txt for keyw in doc.keywords]
            if any(checks):
                random_msg = choice(doc.texts)
                send_msg(msg['sender']['id'], random_msg)
                return True
        return False


class PostBackProc:

    def __init__(self, entry, session=None):
        logger.debug(
            'postback payload {}'.format(entry['postback']['payload']))
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
            bot._typing_indicate()
            time.sleep(1)
            bot.say(txt1)
            bot._typing_indicate()
            time.sleep(2)
            bot.say(txt2, quick_replies=[quickreply])
            bot.get_userinfo()
        if entry['postback']['payload'] == 'start':
            bot = FbManage(entry['sender']['id'])
            bot.start()
        elif entry['postback']['payload'] == 'stop':
            bot = FbManage(entry['sender']['id'])
            bot.deactivate()
            logger.info('user deactivated via postback')
        elif entry['postback']['payload'].startswith('$'):
            logger.info(
                'got echo: {}'.format(entry['postback']['payload'][1:]))
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
    bot._typing_indicate()
    time.sleep(0.5)
    try:
        msg.pop('options')
    except KeyError:
        # no options found
        pass

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


@celery_tasks.celeryapp.task(ignore_result=False, bind=True)
def send_msgs(self, fbid, msg_iter):
    ''' given a user if and a msg iterator, send them all consecutively'''
    # assign appropriate send function for types of msg
    # this function assumes a strucuture built in the models.py section
    db.mdb.connect('database', host=environ.get('MONGODB_URI'))

    try:
        user_file = db.FbUserInfo.objects.get(fb_id=fbid)
        try:
            user_file.tasks.remove(self.request.id)
            user_file.save()
            logger.warning('removed task send_msgs: {}'.format(
                self.request.id))
        except ValueError:
            # value not found
            pass
        for msg in msg_iter:

            if user_file.activated:
                try:
                    tmp = msg.pop('pause')
                except KeyError:
                    tmp = None
                send_msg(fbid, msg)
                # pause for x amount of seconds
                if tmp:
                    logger.warning('pausing')
                    task = send_msgs.apply_async(args=[fbid, msg_iter],
                                                 countdown=int(tmp))
                    user_file.tasks += [task.task_id]
                    user_file.save()
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
    copy_ver = db.FbMsgrTexts.objects().get(day=0)
    events = copy_ver.events
    send_msgs.delay(userinfo['fb_id'], events[0]['msgs'])


@celery_tasks.celeryapp.task(ignore_result=False, bind=True)
def recurse(self, fb_obj, userinfo):
    ''' recursevly calls itself to iterate through all documents
    type FbMsgrTexts (contains text/media to send) in the NoSql database.
    At the end it will signal that the iteration is done by changing
    'activated' field of a user in FbUserInfo
    '''
    db.mdb.connect('database', host=environ.get('MONGODB_URI'))
    try:
        day = next(fb_obj)
    except StopIteration:
        logger.info('days are done')
        user = db.FbUserInfo.objects.get(fb_id=userinfo['fb_id'])
        user.activated = False
    else:
        user = db.FbUserInfo.objects.get(fb_id=userinfo['fb_id'])
        # remove consumed task id from db

        now = datetime.now(timezone(userinfo['timezone']))
        if user.activated:

            logger.warning("recurse on day: {}".format(day))
            doc = db.FbMsgrTexts.objects().get(day=day)
            send_msgs.delay(userinfo['fb_id'], doc.events[0]['msgs'])
            subtasks = []
            msgs_future = now + hour_tdelta

            for evnt in doc.events[1:]:
                # the idea is to async schedule events through out the day
                logger.warning(evnt['msgs'])

                task = send_msgs.apply_async(args=[userinfo['fb_id'], evnt['msgs']],
                                             eta=msgs_future)

                logger.info(evnt['msgs'])
                # put scheduled task id into db
                logger.debug('SEND_MSGS task: {}'.format(task.task_id))
                subtasks.append(task.task_id)
                msgs_future += hour_tdelta

            task = recurse.apply_async(args=[fb_obj, userinfo],
                                     eta=(now + day_tdelta))

            #subtasks.append(task.task_id)
            logger.warning('tasks spawned by recurse: {}'.format(subtasks))
            user.tasks += subtasks
        try:
            user.tasks.remove(self.request.id)
            logger.warning('removed task recurse: {}'.format(self.request.id))
        except ValueError:
            # value not found
            pass
        user.save()

## sub class celery task to track id
## sub class to use one connection