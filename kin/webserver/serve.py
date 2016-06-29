from flask import Flask, request, Response, redirect

import os
import logging

from kin.database.models import TeamCredits
from kin.main import main
from kin.messaging.slack_msgr import SlackMessenger
from kin.messaging.fb_msgr import FbMessenger, startupday1
from mongoengine import errors

app = Flask(__name__)
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@app.route('/' + str(os.environ.get('FB_ENDPOINT')), methods=['GET', 'POST'])
def facebook():
    ''' 
    This function responds to GET and POST at an obfuscated URL.
        GET method  : used exclusively for authentication of webhooks using
                      facebook api dashboard
        POST method : all facebook messages are POSTed to this endpoint
    '''

    if request.method == 'GET':
        if request.args.get('hub.verify_token') == 'becauseoftheimplication':

            return Response(request.args.get('hub.challenge'))

        else:

            return Response("Error invalid token or you're in the wrong neighborhood!")
            logger.info('unautherized access of webhook page')

    if request.method == 'POST':
        # Facebook recommends going through every entry since they might send
        # multiple messages in a single call during high load
        form = request.json
        for entry in form['entry']:
            for message in entry['messaging']:

                # check if a text was sent
                cond2 = message['recepient']['id']
                if 'text' in message['message'] and :
                    if 'ready' in message['message']['text'].lower():
                        bot = FbMessenger(message['sender']['id'])
                        bot.say('activated!')
                        logger.debug(
                            'ready command from user:{}'.format(bot.fbid))
                        userinfo = bot.get_userinfo()
                        startupday1.delay(userinfo)
                    else:
                        bot = FbMessenger(message['sender']['id'])
                        bot.say('sup')

                else:
                    bot = FbMessenger(message['sender']['id'])
                    bot.say('still in developement!')
        
        return Response()




@app.route('/' + str(os.environ.get('SLACK_ENDPOINT')))
def slackauth():
    '''
    This function only responds to GET at an obfuscated url.
    GET method: pass query with 'code' parameter
    '''
    if request.args.get('code'):
        try:
            resp = SlackMessenger.oauth.access(os.environ.get('SLACK_CLIENT'),
                                               os.environ.get('SLACK_SECRET'),
                                               request.args.get('code'))
            if resp.error:
                logger.info('failed authentication')
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
                logger.info('update token for' + resp['team_name'])
                TeamCredits.objects(
                    team_id=resp['team_id']).modify(upsert=True, new=True,
                                                    set__bot_token=resp['bot']['bot_access_token'])
                new_bot = main.StartupBot(resp['bot']['bot_access_token'])
                return redirect('https://telegram.org/')
            # create and run bot program
            logger.info('new bot created for ' + resp['team_name'])
            new_bot = main.StartupBot(resp['bot']['bot_access_token'])
            new_bot.run()
            # redirect to launch success page
            return redirect('http://www.google.com')

        # general exception catching is not good
        except Exception as error:
            # error page
            logger.error("ERROR: " + str(error))
            return redirect('http://www.reddit.com')
    else:
        # wrong page
        logger.info('someone just peeked into slack autherization page!')
        return redirect('http://www.stackoverflow.com')


port = os.getenv('PORT', '8000')
if __name__ == "__main__":
    logger.info('Running Flask server at 0.0.0.0:{}'.format(port))
    app.run(host='0.0.0.0', port=int(port))
