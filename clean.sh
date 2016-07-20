#!/usr/bin/env bash

# only to be used if celery workers are refusing to exit
ps auxww | grep 'celery' | awk '{print $2}' | xargs kill -9