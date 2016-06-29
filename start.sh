#!/usr/bin/env bash

# please properly daemonize these celery worker and scheduler and use CPU cores
export PYTHONPATH=$PWD
python3 setup.py



# confirm ALCHEMY API key
python3 kin/cognitive/cognitive.py
mv api_key.txt kin/cognitive

# run celery scheduler
celery -A kin.scheduling.celery_tasks beat -S celerybeatmongo.schedulers.MongoScheduler --loglevel=INFO &

# run celery worker in background
celery -A kin.scheduling.celery_tasks worker \
        --without-gossip --without-mingle \
        --without-heartbeat --loglevel=INFO & 

# run flask server
python3 kin/webserver/serve.py