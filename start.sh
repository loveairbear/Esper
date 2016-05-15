#!/usr/bin/env bash

# please properly daemonize these celery worker and scheduler
export PYTHONPATH=$PWD
python3 setup.py
python3 kin/cognitive/cognitive.py
mv api_key.txt kin/cognitive
celery -A kin.scheduling.celery_tasks beat -S celerybeatmongo.schedulers.MongoScheduler --loglevel=INFO &
celery -A kin.scheduling.celery_tasks worker --without-gossip --without-mingle --without-heartbeat --loglevel=INFO &
python3 kin/main/reqserve.py