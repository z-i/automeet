from flask import Flask, request
import json

from db import table

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
    user_info['tokens'] = tokens
    user_info['user_id'] = user_info['id']
    table.put_item(
        Item = user_info
    )
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
    token_json = table.get_item(
        Key = {
            'user_id': user_id
        }
    )
    token_json = token_json['Item']['tokens']
    cred = OAuth2Credentials.from_json(token_json)
    http = cred.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    car = service.calendarList().list().execute()
    car = [x['id'] for x in (car['items'])]
    return json.dumps({'calendars':car})

@app.route("/free")
def get_freetime():
 
    
    user_id = request.args.get('user_id', )
    timeMin = request.args.get('timeMin', )
    timeMax = request.args.get('timeMax', )

    friend_list = ['108219253602729852661', '115974855826456350106']

    available_friend = []
    
    for x in friend_list:
        fr, _ = get_busy(x, timeMin, timeMax)
        if fr:
            available_friend.append(x)

    return json.dumps({'available_friends':available_friend})

def get_busy(user_id, timeMin, timeMax):
    token_json = table.get_item(
        Key = {
            'user_id': user_id
        }
    )
    token_json = token_json['Item']['tokens']
    cred = OAuth2Credentials.from_json(token_json)
    http = cred.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    calendar = service.calendarList().list().execute()
    calendar = [{'id':x['id']} for x in (calendar['items'])]
    calendar = service.freebusy().query(body={
        'timeMin': timeMin,
        'timeMax': timeMax,
        'items' : calendar,
        'timeZone': '-05:00'
    }
    ).execute()
    calendar['busy_status'] = is_free_time(calendar)   

    return calendar['busy_status'], calendar 

def is_free_time(freebusyCar):
    busys = []
    for x in freebusyCar['calendars'].values():
        if x['busy'] != [] :
            return False
    return True


# @app.route("/tokens")
# def get_tokens():
#     user_id = 
#     tokens = 
if __name__ == "__main__":
    app.run(debug=True, port=5001)