#!/usr/bin/env bash
export PYTHONPATH=$PWD
python3 setup.py

python3 kin/cognitive/cognitive.py
mv api_key.txt kin/cognitive

cd kin/scheduling
celery -A celery_tasks beat -S celerybeatmongo.schedulers.MongoScheduler --loglevel=INFO &
celery -A celery_tasks worker \
    --without-gossip --without-mingle --without-heartbeat --loglevel=INFO 



