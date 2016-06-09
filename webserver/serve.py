from flask import Flask, request, Response,redirect
import os

import json
import requests


from kin.database.models import TeamCredits
from kin.main import main
from kin.messaging.slack_messenger import SlackMessenger
from mongoengine import errors

app = Flask(__name__)


@app.route('/'+str(os.environ.get('FB_ENDPOINT')), methods=['GET', 'POST'])
def facebook():
    if request.method == 'GET':
        if request.args.get('hub.verify_token') == 'becauseoftheimplication':
            return Response(request.args.get('hub.challenge'))

        else:
            return Response('Error invalid token or youre in the wrong neighborhood!')
   
    if request.method == 'POST':
        print('IN POST')
        # Facebook recommends going through every entry since they might send
        # multiple messages in a single call during high load
        form = request.json

        for entry in form['entry']:
            for message in entry['messaging']:
                # Check to make sure the received call is a message call
                # This might be delivery, optin, postback for other events
                if 'message' in message:
                    # Print the message to the terminal
                    print(message['message']['text'])
                    # echo the message
                    post_facebook_message(message['sender']['id'], 'sup')
        return Response()

def post_facebook_message(fbid, received_message):
    post_message_url = 'https://graph.facebook.com/v2.6/me/messages?access_token=' + \
        os.environ.get('FB_TOKEN')
    response_msg = json.dumps(
        {"recipient": {"id": fbid}, "message": {"text": received_message}})

    status = requests.post(
        post_message_url,
        headers={"Content-Type": "application/json"},
        data=response_msg)

    print(fbid)
    print(status.json())



@app.route('/'+str(os.environ.get('SLACK_ENDPOINT')))
def slackauth():

    if request.args.get('code'):
        try:
            resp = SlackMessenger.oauth.access(os.environ.get('SLACK_CLIENT'),
                                               os.environ.get('SLACK_SECRET'),
                                               request.args.get('code'))
            if resp.error:
                print('auth failed')
                raise Exception('failed authentication')

            resp = resp.body
            # save team authentication
            entry = TeamCredits(team_name=resp['team_name'],
                                team_id=resp['team_id'],
                                bot_userid=resp['bot']['bot_user_id'],
                                bot_token=resp['bot']['bot_access_token'])
            try:
                entry.save()
            except errors.NotUniqueError:
                # update bot_token
                TeamCredits.objects(
                    team_id=resp['team_id']).modify(upsert=True, new=True,
                                                    set__bot_token=resp['bot']['bot_access_token'])
                new_bot = main.StartupBot(resp['bot']['bot_access_token'])
                return redirect('https://telegram.org/')
            # create and run bot program
            new_bot = main.StartupBot(resp['bot']['bot_access_token'])
            new_bot.run()
            # redirect to launch success page
            return redirect('http://www.google.com')

        # general exception catching is not good
        except Exception as error:
             # error page
            print("ERROR: " + str(error))
            return redirect('http://www.reddit.com')
    else:
        # wrong page
        return redirect('http://www.stackoverflow.com')


port = os.getenv('PORT', '8000')
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(port))
