#!/usr/bin/python
import os
import json
from subprocess import call

if os.environ.get('VCAP_SERVICES'):
    api_keys = json.loads(os.environ.get('VCAP_SERVICES'))
    for key in api_keys.keys:
        if key == 'alchemy_api':
            call(
                ['python3', 'esper/alchemySDK/alchemyapi.py',
                 key['credentials']['apikey']])
elif os.environ.get('ALCHEMY_API'):
    call(
        ['python3', 'esper/alchemySDK/alchemyapi.py',
         os.environ.get('ALCHEMY_API')])
else:
    print('You need an ALCHEMY_API key for full functionality')

