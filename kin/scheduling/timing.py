# experimental with fluid timing,
# rather than hardcoding the timing can change with database
'''
@celery_tasks.celeryapp.task
def startupday1(userinfo):
    logger.debug('startupday1')
    events = next(db.FbMsgrTexts.objects(day=1)).events
    eta = datetime.now(timezone(userinfo['timezone']))
    send_msgs.delay(userinfo['user_id'], events[0]['msgs'])
    for evnt in events[1:]:
        # the idea is to aync schedule events through out the day
        send_msgs.apply_async(args=[userinfo['user_id'], evnt['msgs']],
                              eta=eta + hour_tdelta)

    #future = eta.replace(day=eta.day + 1, hour=12, minute=0)
    future = eta + day_tdelta
    user_file = next(db.FbUserInfo.objects(user_id=userinfo['user_id']))
    if user_file.activated:
        startupday2.apply_async(args=[userinfo], eta=future)
'''

class Event:
    def __init__(self,time,func,**kwargs):
        self._time = time
        self.func = func
        self.func_args = kwargs.get('args')
    




# create a list from events