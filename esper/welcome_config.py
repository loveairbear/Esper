import requests
import json
from os import environ

# sets up getting started buttons and welcome message

token = environ.get('FB_TOKEN')
post_message_url = 'https://graph.facebook.com/v2.6/me/thread_settings?access_token={}'.format(
    token)
response_msg = json.dumps({
    "setting_type": "call_to_actions",
    "thread_state": "new_thread",
    "call_to_actions": [{
        "payload": "intro"
    }
    ]
})
status = requests.post(post_message_url,
                       headers={"Content-Type": "application/json"},
                       data=response_msg)

print(status.text)

'''
greeting = json.dumps({
    "setting_type": "greeting",
    "greeting": {
        "text": "welcome to Stanson!"
    }
})

status = requests.post(post_message_url,
                       headers={"Content-Type": "application/json"},
                       data=greeting)

print(status.text)
'''
response_msg = json.dumps({
    "setting_type": "call_to_actions",
    "thread_state": "existing_thread",
    "call_to_actions": [{
        "payload": "stop",
        "title": "Leave course",
        "type": "postback",
    }, {
        "payload": "start",
        "title": "Begin course",
        "type": "postback",
    }
    ]
})
status = requests.post(post_message_url,
                       headers={"Content-Type": "application/json"},
                       data=response_msg)
print(status.text)