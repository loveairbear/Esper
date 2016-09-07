#!/usr/bin/env bash


# cleanup since celery does not exit properly
ps auxww | grep 'celery' | awk '{print $2}' | xargs kill -9


# please properly daemonize these celery worker and scheduler and use CPU cores
export PYTHONPATH=$PWD
python3 setup.py

# python3 kin/scheduling/celery_logging.py &

# confirm ALCHEMY API key
python3 esper/cognitive/cognitive.py
mv api_key.txt esper/cognitive




 
# run celery scheduler
celery -A esper.scheduling.celery_tasks beat -S celerybeatmongo.schedulers.MongoScheduler --loglevel=INFO &

# run celery worker in background
celery  -A esper.scheduling.celery_tasks worker \
        --without-gossip --without-mingle \
        --without-heartbeat --loglevel=INFO \
        --autoscale=10,3 -Ofair --concurrency=4 &

# run flask server

python3 esper/webserver/serve.py 

