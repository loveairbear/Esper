from http import server
from os import environ
from urllib.parse import parse_qs, urlparse

from kin.database.models import TeamCredits
from kin.main import main
from kin.messaging.slack_messenger import SlackMessenger
from mongoengine import errors

class MyHandler(server.BaseHTTPRequestHandler):

    def do_HEAD(self):
        print('in head')
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self):
        """Respond to a GET request."""
        self.send_response(301)
        # We cant have any caches
        self.send_header(
            "Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        # parse query
        params = parse_qs(urlparse(self.path).query, keep_blank_values=True)
        if params.get('code'):
            try:
                resp = SlackMessenger.oauth.access(environ.get('SLACK_CLIENT'),
                                                   environ.get('SLACK_SECRET'),
                                                   params['code'])
                if resp.error:
                    raise Exception('failed authentication')

                resp = resp.body

                entry = TeamCredits(team_name=resp['team_name'],
                                    team_id=resp['team_id'],
                                    bot_userid=resp['bot']['bot_user_id'],
                                    bot_token=resp['bot']['bot_access_token'])
                try:
                    entry.save()
                except errors.NotUniqueError:
                    TeamCredits.objects(team_id=resp['team_id']).modify(upsert=True, new = True,
                                                                        set__bot_token =resp['bot']['bot_access_token'])

                new_bot = main.StartupBot(resp['bot']['bot_access_token'])
                main.BOTS.add(new_bot)
                new_bot.run()
                # redirect to launch success page
                self.send_header('Location', 'http://www.google.com')
                self.end_headers()
                print('saved!!')
                return
            except Exception as error:
                # error page
                print("ERROR: " + error)
                self.send_header('Location', 'http://www.reddit.com')
                self.end_headers()
        else:
            # wrong page
            self.send_header('Location', 'http://www.stackoverflow.com')
            self.end_headers()

    def do_POST(self):
        print('in POST')

if __name__ == '__main__':
    if environ.get('PORT'):
        port = environ.get('PORT')
    else:
        port = 3000
    server_address = ('', port)
    httpd = server.HTTPServer(server_address, MyHandler)
    print("Server Starts - %s:%s" % server_address)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print("Server Stops - %s:%s" % server_address)
