# data collection models

# authentication models
import mongoengine as mongdb
from os import environ
mongodb = mongdb.connect(
    'database', host=environ.get('MONGODB_URI'))


class TeamCredits(mongdb.DynamicDocument):
    meta = {'collection': 'slackteams',
            'allow_inheritance': True}

    team_name = mongdb.StringField(required=True)
    team_id = mongdb.StringField(required=True, unique=True)
    bot_userid = mongdb.StringField(required=True)
    bot_token = mongdb.StringField(required=True, unique=True)


