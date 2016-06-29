# data collection models

# authentication models
import mongoengine as mongodb
from os import environ

from celerybeatmongo.models import PeriodicTask
from celery.schedules import crontab
db = mongodb.connect(
    'database', host=environ.get('MONGODB_URI'))

# Periodic schedule that can be inserted and executed dynamically
class CelerySchedule:

    def remove(task_name):
        PeriodicTask.objects(task_name=task_name).delete()

    def insert(self, task_name, task, args, cron, offset):
        task = str(task)
        task_name = str(task_name)
        # the celery scheduler runs on UTC time, add offset so that it
        # emulates the user timezone
        cron.hour = set(map(lambda x: (x - (offset)) % 24, cron.hour))

        # if the integer overflows should a day advance? or will the overflow only when
        # UTC time is > 12 therefore the next time a time < 12 occurs is on the
        # next day?

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
class TeamCredits(mongodb.DynamicDocument):
    meta = {'collection': 'slackteams',
            'allow_inheritance': True}
    team_name = mongodb.StringField(required=True)
    team_id = mongodb.StringField(required=True, unique=True)
    bot_userid = mongodb.StringField(required=True)
    bot_token = mongodb.StringField(required=True, unique=True)


class UserData(mongodb.DynamicDocument):
    meta = {'collection': 'userprofiles',
            'allow_inheritance': True}
    user_id = mongodb.StringField(required=True, unique=True)
    user_tz = mongodb.StringField(required=True)
    num_timeouts = mongodb.IntField()
    res_freq = mongodb.ListField()
    enabled = mongodb.BooleanField(default=True)


# Facebook
class FbUserInfo(mongodb.DynamicDocument):
    meta = {'collection': 'fb_users',
            'allow_inheritance': True}
    user_id = mongodb.StringField(required=True,unique=True)
    timezone = mongodb.StringField(required=True)
    gender = mongodb.StringField(required=True)
    name = mongodb.StringField()
    optout = mongodb.BooleanField(default=False)

    def save(self):
        try:
            super().save()
        except mongodb.errors.NotUniqueError:
            # don't need to update?
            pass
