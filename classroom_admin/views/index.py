import os
import csv

import flask
from flask import render_template
from oauth2client import client

from .. import app
from .. import socketio


@app.route('/')
def index():
    if 'credentials' not in flask.session:
        return flask.redirect(flask.url_for('oauth2callback'))

    credentials = client.OAuth2Credentials.from_json(
        flask.session['credentials'])

    if credentials.access_token_expired:
        return flask.redirect(flask.url_for('oauth2callback'))
    else:
        filename = os.path.join(app.config['UPLOAD_FOLDER'], 'courses_list.csv')
        if os.path.isfile(filename):
            with open(filename) as csvfile:
                reader = csv.DictReader(csvfile)
                try:
                    return render_template('courses.html',
                                           courses=reader,
                                           conf=app.config['COURSE_CONF'])
                except Exception:
                    error_message = "Some characters in the file are not in " \
                        "UTF-8. Please check your file and remove non-unicode " \
                        "characters."
                    return render_template('index.html',
                                           error_message=error_message)
        else:
            return render_template('index.html')


@socketio.on('confirm')
def test_message(message):
    print('Socket: received confirmation message: ' + message['data'])


@socketio.on('connect')
def test_connect():
    print('Socket: Got connected to client')


@socketio.on('disconnect')
def test_disconnect():
    print('Socket: Client disconnected')
