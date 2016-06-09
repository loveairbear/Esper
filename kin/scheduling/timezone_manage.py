from datetime import datetime, timedelta
import pytz

# do edge case of daylight savings transition
# which raise error type  pytz.exceptions.AmbiguousTimeError


def utc_to_tz(gmtoffset):
    """
    convert utc offset to a timezone in Olson format

    :param gmtoffset can be an unsigned integer or float
    """
    offset = timedelta(hours=gmtoffset)
    now = datetime.now()
    if(gmtoffset > 14 or gmtoffset < -12):
        raise 'incorrect utc offset'
    for tz in map(pytz.timezone, pytz.common_timezones_set):
        if tz.utcoffset(now) == offset:
            return str(tz)
