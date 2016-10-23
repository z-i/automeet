from flask import Flask, request, render_template, send_from_directory
import json
import decimal
import datetime


from db import table, friend_table

from oauth2client.client import OAuth2WebServerFlow, OAuth2Credentials
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
import time

import httplib2

class TZ(datetime.tzinfo):
    def utcoffset(self, dt):
        return datetime.timedelta(hours=-5)
    def dst(self, dt):
        return datetime.timedelta(0)

app = Flask(__name__, static_url_path='/images')
flow = OAuth2WebServerFlow(client_id='394673669484-ffcdcejgcj397gmkijpgk3hh3dc7vibu.apps.googleusercontent.com',
                           client_secret='2BOy3uYnYVVlkE7SIvm59hN1',
                           scope=['https://www.googleapis.com/auth/plus.me', 'https://www.googleapis.com/auth/calendar'],
                           redirect_uri='http://localhost:5001/oauthcb/')

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


@app.route("/friends")
def list_friends():
    return json.dumps(get_friend(),indent=4, cls=DecimalEncoder)

# @app.route("/friend/add")
# def add_friend():
#     email = request.args.get('email',)
#     return

def get_friend():
     resp = table.scan(ProjectionExpression= "user_id")
     friends = [x['user_id'] for x in resp['Items']]
     return friends

@app.route("/info")
def get_info():
    user_id = request.args.get('user_id',)
    info = table.get_item(
        Key = {
            'user_id': user_id
        }
    )
    return json.dumps(info['Item'],indent=4, cls=DecimalEncoder)

def get_name(user_id):
    info = table.get_item(
        Key = {
            'user_id': user_id
        }
    )
    return info['Item']['displayName']

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

    friend_list = get_friend()

    available_friend = []
    
    for x in friend_list:
        fr, _ = get_busy(x, timeMin, timeMax)
        if fr:
            available_friend.append(x)

    return json.dumps({'available_friends':available_friend})


def get_free_time(timeMin, timeMax):
    friend_list = get_friend()
    available_friend = []
    
    for x in friend_list:
        fr, _ = get_busy(x, timeMin, timeMax)
        if fr:
            available_friend.append(x)
    return available_friend

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

@app.route("/makeAppt")
def make_appt():
    times = []
    for x in range(5):
        timeMin = datetime.datetime.combine(datetime.date.today(), datetime.time(hour = x + datetime.datetime.now(tz=TZ()).hour)).isoformat() + "-05:00"
        timeMax = datetime.datetime.combine(datetime.date.today(), datetime.time(hour = x + 1 + datetime.datetime.now(tz=TZ()).hour)).isoformat() + "-05:00"
        aval_friends = get_free_time(timeMin, timeMax)
        names = []
        for f in aval_friends:
            names.append(get_name(f))
        time = {
            "timeMin": timeMin,
            "frees": names,
        }
        times.append(time)
    return render_template('makeAppointment.html', times = times)

@app.route('/')
def inde_page():
    return render_template('index.html')

# @app.route('/images/<path:path>')
# def send_js(path):
#     return send_from_directory('images', path)

@app.route('/images/<path:path>')
def static_proxy(path):
  # send_static_file will guess the correct MIME type
  return app.send_static_file(path)

# @app.route("/tokens")
# def get_tokens():
#     user_id = 
#     tokens = 
if __name__ == "__main__":
    app.run(debug=True, port=5001)