#!/usr/bin/python
import sys
import os
import json
from subprocess import call

if os.environ.get('VCAP_SERVICES'):
    keys = json.loads(os.environ.get('VCAP_SERVICES'))
    for key in keys:
        if key == 'alchemy_api':
            call(
                ['python3', 'kin/alchemySDK/alchemyapi.py',
                 key['credentials']['apikey']])
else:
    call(
        ['python3', 'kin/alchemySDK/alchemyapi.py',
         os.environ.get('ALCHEMY_API')])


# sys.path.append(os.getcwd() + '/kin')
