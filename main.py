from flask import Flask, request
import json

from db import db_client

from oauth2client.client import OAuth2WebServerFlow, OAuth2Credentials
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
import time

import httplib2

app = Flask(__name__)
flow = OAuth2WebServerFlow(client_id='394673669484-ffcdcejgcj397gmkijpgk3hh3dc7vibu.apps.googleusercontent.com',
                           client_secret='2BOy3uYnYVVlkE7SIvm59hN1',
                           scope=['https://www.googleapis.com/auth/plus.me', 'https://www.googleapis.com/auth/calendar'],
                           redirect_uri='http://localhost:5001/oauthcb/')


@app.route("/oauthcb/")
def oauth_callback():
    code = request.args.get('code', )
    credentials = oauth(code)
    with open('cred.json', 'w') as c:
        c.write(credentials.to_json())
    user_info = get_user_info(credentials)
    tokens = credentials.to_json()
    resp = db_client.put("users", user_info['id'], user_info)
    resp2 = db_client.put("tokens", user_info['id'], {"t":tokens})
    return "hi";

def oauth(code):
    credentials = flow.step2_exchange(code +"#")
    return credentials

def get_user_info(cred):
    http = cred.authorize(httplib2.Http())
    service = discovery.build('plus', 'v1', http=http)
    return service.people().get(userId = 'me').execute()

@app.route("/get_auth")
def get_auth_url():
    auth_uri = flow.step1_get_authorize_url()
    return auth_uri

@app.route("/calendars")
def get_calendars():
    user_id = request.args.get('user_id', )
    # timeMin = request.args.get('timeMin', )
    # timeMax = request.args.get('timeMax', )
    # calendar = request.args.get('calendar', )
    token_json = (db_client.get('tokens', user_id).json['t'])

    cred = OAuth2Credentials.from_json(token_json)
    http = cred.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    return service.calendarList().list().execute()


# @app.route("/tokens")
# def get_tokens():
#     user_id = 
#     tokens = 
if __name__ == "__main__":
    app.run(debug=True, port=5001)