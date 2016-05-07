import mongoengine
from celerybeatmongo.models import PeriodicTask
from os import environ
from celery.schedules import crontab
mongodb = mongoengine.connect(
    'database', host=environ.get('MONGODB_URI'))


class CelerySchedule:

    def __init__(self):
        pass

    def remove(task_name):
        PeriodicTask.objects(task_name=task_name).delete()

    def insert(self, task_name, task, args, cron,offset):
        task = str(task)
        task_name = str(task_name)
        # the celery scheduler runs on UTC time, add offset so that it 
        # emulates the user timezone
        cron.hour = set(map(lambda x: (x - (offset)) % 24, cron.hour))
        # if the integer overflows should a day advance? or will the overflow only when
        # UTC time is > 12 therefore the next time a time < 12 occurs is on the next day?

        cronArr = [cron.minute,
                   cron.hour,
                   cron.day_of_week, cron.
                   day_of_month,
                   cron.month_of_year]
        # cron.minute return {number}, change to 'number' for celery schedule
        for i in cronArr:
          i = str(i).replace('{','').replace('}','')
          print(i)




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
        # addTask.save()
if __name__ == '__main__':
    ok = CelerySchedule()
    ok.insert('task1', 'celery_tasks.sss', [], crontab(hour=[2, 9, 14, 19]), -4)
