from datetime import datetime
import pytz


def utc_to_tz(gmtoffset):
    now = datetime.now(pytz.utc)
    for tz in map(pytz.timezone, pytz.common_timezones_set):
        if(datetime.now(tz).hour - now.hour == gmtoffset):
            return str(tz)
