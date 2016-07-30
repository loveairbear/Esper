import os
import logging
import argparse

from flask import Flask, request, Response, redirect
from mongoengine import errors


from kin.database.models import TeamCredits
from kin.main import main
from kin.messaging.slack_msgr import SlackMessenger
from kin.messaging import fb_msgr as fb


app = Flask(__name__)


# handle logging and such
parser = argparse.ArgumentParser()
parser.add_argument(
    '-l', '--log',
    help="log level : DEBUG/INFO/WARNING/ERROR/CRITICAL",
    choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
    dest="loglevel"
)
args = parser.parse_args()

root_logger = logging.getLogger()


# instantiate root logger
root_logger = logging.getLogger()
if args.loglevel:
    root_logger.setLevel(args.loglevel)
else:
    root_logger.setLevel(logging.INFO)

if os.environ.get('LOG_ADDR') and os.environ.get('LOG_PORT'):
    addr = os.environ.get('LOG_ADDR')
    addr_port = int(os.environ.get('LOG_PORT'))
    syslog = logging.handlers.SysLogHandler(address=(addr, addr_port))
    root_logger.addHandler(syslog)

logger = logging.getLogger('Flask-Webserver')
logger.setLevel(logging.DEBUG)


@app.route('/' + str(os.environ.get('FB_ENDPOINT')), methods=['GET', 'POST'])
def facebook():
    '''
    This function responds to GET and POST at an obfuscated URL.
        GET method  : used exclusively for authentication of webhooks using
                      facebook api dashboard
        POST method : all facebook messages are POSTed to this endpoint
                      and processed asyncronously using Celery
    '''

    if request.method == 'GET':
        if request.args.get('hub.verify_token') == 'becauseoftheimplication':
            logger.info('authenticated')
            return Response(request.args.get('hub.challenge'))

        else:

            return Response("Error invalid token or you're in the wrong neighborhood!")
            logger.info('unautherized access of webhook page')

    if request.method == 'POST':
        form = request.json
        logger.debug(form)
        for entry in form['entry']:
            for messaging in entry['messaging']:
                # async task call
                fb.FbHandle.apply_async(args=[messaging], expires=15, retry=False)
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



if __name__ == "__main__":
    port = os.getenv('PORT', '8000')
    logger.info('Running Flask server at 0.0.0.0:{}'.format(port))
    logger.debug('DEBUG IS ON')
    app.run(host='0.0.0.0', port=int(port))
