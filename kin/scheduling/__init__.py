import logging
import os
from celery.signals import after_setup_task_logger, after_setup_logger

def setup_handler(sender=None, logger=None, loglevel=None,
       logfile=None, fmt=None, colorize=None, **kwds):
    """create a syslog handler"""
    addr = os.environ.get('LOG_ADDR',None)
    addr_port = os.environ.get('LOG_PORT',None)
    if addr and addr_port:
        handler = logging.handlers.SysLogHandler(address=(addr, int(addr_port)))
        handler.setFormatter(logging.Formatter(fmt))
        handler.setLevel(loglevel or logging.DEBUG)
        logger.addHandler(handler)

after_setup_logger.connect(setup_handler)
after_setup_task_logger.connect(setup_handler)