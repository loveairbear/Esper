from celery.app.log import Logging

import logging
import os
from celery.signals import after_setup_task_logger, after_setup_logger

def setup_handler(sender=None, logger=None, loglevel=None,
       logfile=None, fmt=None, colorize=None, **kwds):
    """create a syslog handler"""
    addr = os.environ.get('LOG_ADDR')
    addr_port = int(os.environ.get('LOG_PORT'))
    handler = logging.handlers.SysLogHandler(address=(addr, addr_port))
    handler.setFormatter(logging.Formatter(fmt))
    handler.setLevel(loglevel or logging.DEBUG)
    logger.addHandler(handler)

after_setup_logger.connect(setup_handler)
after_setup_task_logger.connect(setup_handler)