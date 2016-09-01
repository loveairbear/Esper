import mongoengine as mdb
from os import environ

from celerybeatmongo.models import PeriodicTask
db = mdb.connect(
    'database', host=environ.get('MONGODB_URI'))



class CelerySchedule:
    '''
    Periodic schedule that can be inserted and executed dynamically
    '''
    def remove(task_name):
        ''' remove database entry using task_name as lookup'''
        next(PeriodicTask.objects(task_name=task_name)).delete()

    def insert(self, task_name, task, args, cron, offset):
        ''' insert a periodic task into database
        params: task_name : string
                task: a registered task in celery workers
                args: task arguments
                cron: crontab object
                offset: UTC offset
        '''
        task = str(task)
        task_name = str(task_name)
        # the celery scheduler runs on UTC time, add offset so that it
        # emulates the user timezone
        cron.hour = set(map(lambda x: (x + (offset)) % 24, cron.hour))

        # if the integer overflows should a day advance? or will the overflow
        # only when UTC time is > 12 therefore the next time a time < 12
        # occurs is on the next day?

        cronArr = [cron.minute,
                   cron.hour,
                   cron.day_of_week, cron.
                   day_of_month,
                   cron.month_of_year]
        # cron.minute return {number}, change to 'number' for celery schedule
        for i in range(len(cronArr)):
            cronArr[i] = str(cronArr[i]).replace('{', '')
            cronArr[i] = cronArr[i].replace('}', '')

        # following mongocelerybeat document schema for schedules
        addTask = PeriodicTask()
        addTask.name = task_name
        addTask.task = task
        addTask.crontab = addTask.Crontab(minute=cronArr[0],
                                          hour=cronArr[1],
                                          day_of_week=cronArr[2],
                                          day_of_month=cronArr[3],
                                          month_of_year=cronArr[4])

        addTask.enabled = True
        addTask.args = args
        addTask.save()

# SLACK
class TeamCredits(mdb.DynamicDocument):
    meta = {'collection': 'slackteams'}
    team_name = mdb.StringField(required=True)
    team_id = mdb.StringField(required=True, unique=True)
    bot_userid = mdb.StringField(required=True)
    bot_token = mdb.StringField(required=True, unique=True)


class UserData(mdb.DynamicDocument):
    meta = {'collection': 'userprofiles'}
    user_id = mdb.StringField(required=True, unique=True)
    user_tz = mdb.StringField(required=True)
    num_timeouts = mdb.IntField()
    res_freq = mdb.ListField()
    enabled = mdb.BooleanField(default=True)

###############################################################################
# Facebook
class FbUserInfo(mdb.DynamicDocument):
    ''' Stores basic user info of facebook user '''
    meta = {'collection': 'fb_users'}
    fb_id = mdb.StringField(required=True, unique=False)
    account = mdb.StringField(unique=True)
    timezone = mdb.StringField(required=True)
    gender = mdb.StringField(required=True)
    name = mdb.StringField()
    optout = mdb.BooleanField(default=False)
    activated = mdb.BooleanField(default=False)



class FbEvents(mdb.EmbeddedDocument):
    
    msgs = mdb.ListField(required=True)


class FbMsgrTexts(mdb.DynamicDocument):
    meta = {'collection': 'fb_msgr_texts',
            'ordering': 'day'}
    day = mdb.IntField(required=True, unique=True)
    events = mdb.EmbeddedDocumentListField(FbEvents)


class RandomMsg(mdb.DynamicDocument):
    meta = {'collection': 'fb_msgr_keywords'}
    texts = mdb.ListField(mdb.StringField())
    keywords = mdb.ListField(mdb.StringField())




if __name__ == '__main__':
    db = mdb.connect('database', host=environ.get('MONGODB_URI'))
    for i in range(3):
        ex = RandomMsg()
        ex.texts = ['testing', 'add words to be randomly chosen','unknown commands']
        ex.keyword = str(i)
        try:
            ex.save()
            print('saved')
        except mdb.errors.NotUniqueError as e:
            print(e)
            print('not saved')
            pass
    # populate collection with 10 startup days as example to edit copy
    for i in range(0, 11):
        print(i)
        obj1 = dict(elems=[dict(title='title', item_url='http://tex.stackexchange.com/questions/173317/is-there-a-latex-wrapper-for-use-in-google-docs',
                      image_url='https://s-media-cache-ak0.pinimg.com/736x/1d/50/94/1d5094b488985c34557942d6867e67e3.jpg')])
        obj2 = dict(text='testing')
        a = FbEvents(msgs=[obj1, obj2])
        b = FbEvents(msgs=[obj1, obj2])
        randy = FbMsgrTexts()
        randy.day = i
        randy.events = [a, b]
        try:
            randy.save()
        except mdb.errors.NotUniqueError:
            pass