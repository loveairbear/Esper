import mongoengine
from celerybeatmongo.models import PeriodicTask
from os import environ

mongodb = mongoengine.connect(
    'database', host=environ.get('MONGODB_URI'))


class CelerySchedule:

    def __init__(self):
        pass

    def remove(task_name):
        PeriodicTask.objects(task_name=task_name).delete()

    def insert(self, task_name, task, args, cron):
        task = str(task)
        task_name = str(task_name)
        cronArr = [cron.minute,
                   cron.hour,
                   cron.day_of_week, cron.
                   day_of_month,
                   cron.month_of_year]
        # cron.minute return {number}, change to 'number' for celery schedule
        for i in range(len(cronArr)):
            strX = str(cronArr[i]).replace('{', "")
            cronArr[i] = strX.replace('}', "")

        # following mongocelerybeat document schema for schedules
        addTask = PeriodicTask()
        addTask.name = task_name
        addTask.task = task
        addTask.crontab = addTask.Crontab(minute=cronArr[0],
                                          hour=cronArr[1],
                                          day_of_week=cronArr[2],
                                          day_of_month=cronArr[3],
                                          month_of_year=cronArr[4]
                                          )

        addTask.enabled = True
        addTask.args = args
        addTask.save()
