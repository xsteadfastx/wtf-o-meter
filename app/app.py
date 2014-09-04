from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template
from flask.ext.socketio import SocketIO
from flask_bootstrap import Bootstrap
import arrow
import json
import threading
import time
import tweepy

# import config
from config import *


app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = SECRET_KEY
Bootstrap(app)
socketio = SocketIO(app)
data = {}
data['history'] = []


class StListener(tweepy.StreamListener):
    def __init__(self):
        super(self.__class__, self).__init__()
        data['count'] = 0
        data['minute'] = arrow.utcnow().format('m')
        data['history'].append({'wtfs per minute': data['count'],
                                'minute': data['minute']})

    def on_status(self, status):
        ''' on new tweet with specific hashtag '''
        data['count'] += 1
        data['history'][-1]['wtfs per minute'] = data['count']
        socketio.emit('my response',
                      json.dumps(data),
                      namespace='/test')
        return True

    def on_error(self, status_code):
        return True

    def on_timeout(self):
        return True


def count_resetter():
    ''' reset the count every minute '''
    while True:
        time.sleep(1)
        if arrow.utcnow().format('m') != data['minute']:
            data['count'] = 0
            data['minute'] = arrow.utcnow().format('m')
            data['history'].append({'wtfs per minute': data['count'],
                                    'minute': data['minute']})
            socketio.emit('my response',
                          json.dumps(data),
                          namespace='/test')


def listen():
    ''' twitter listener '''
    # start stream
    listener = StListener()
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN_KEY, ACCESS_TOKEN_SECRET)
    stream = tweepy.Stream(auth, listener)
    # filter for specific hashtag or word
    stream.filter(track=[HASHTAG])


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('connect', namespace='/test')
def wtfometer_connect():
    print 'Client connected'
    socketio.emit('my response',
                  json.dumps(data),
                  namespace='/test')


@socketio.on('disconnect', namespace='/test')
def hashwall_disconnect():
    print 'Client disconnected'


if __name__ == '__main__':
    threading.Thread(target=listen).start()
    threading.Thread(target=count_resetter).start()
    socketio.run(app)
