import json
import csv
import os

import httplib2
import flask

from apiclient import discovery
from oauth2client import client

from flask import render_template
from flask import Flask
from werkzeug import secure_filename

app = Flask(__name__)

# This is the path to the upload directory
app.config['UPLOAD_FOLDER'] = 'uploads/'
# These are the extension that we are accepting to be uploaded
app.config['ALLOWED_EXTENSIONS'] = set(['csv'])

# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():
    if 'credentials' not in flask.session:
        return flask.redirect(flask.url_for('oauth2callback'))

    credentials = client.OAuth2Credentials.from_json(flask.session['credentials'])

    if credentials.access_token_expired:
        return flask.redirect(flask.url_for('oauth2callback'))
    else:
        http_auth = credentials.authorize(httplib2.Http())
        service = discovery.build('classroom', 'v1', http=http_auth)

        if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], 'courses_list.csv')) :
            with open(os.path.join(app.config['UPLOAD_FOLDER'], 'courses_list.csv')) as csvfile:
                reader = csv.DictReader(csvfile)
                return render_template('courses.html', courses=reader)
        else:
            return render_template('index.html')


@app.route('/create')
def create():
    if 'credentials' not in flask.session:
        return flask.redirect(flask.url_for('oauth2callback'))

    credentials = client.OAuth2Credentials.from_json(flask.session['credentials'])

    if credentials.access_token_expired:
        return flask.redirect(flask.url_for('oauth2callback'))
    else:
        http_auth = credentials.authorize(httplib2.Http())
        service = discovery.build('classroom', 'v1', http=http_auth)
        if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], 'courses_list.csv')) :
            with open(os.path.join(app.config['UPLOAD_FOLDER'], 'courses_list.csv')) as csvfile:
                reader = csv.DictReader(csvfile)
                course = next(reader)

                print('%'*80)
                print(course)

                # Create course
                body = {
                    'ownerId': course['Moderateur'],
                    'name': course['Cours'],
                    'section': course['Année scolaire'] + ' - ' + course['Domaine'] + ' - ' + course['Promotion'],
                    'courseState': 'ACTIVE'
                }

                result = service.courses().create(body=body).execute()

                print('*'*80)
                print(result)

                # Add teacher to course
                teacher = {
                    'courseId': result['id'],
                    'userId': course['Mail wsf de l\'intervenant'],
                    'role': 'TEACHER'
                }

                try:
                    service.invitations().create(body=teacher).execute()
                    print (u'User {0} was added as a teacher to the course with ID "{1}"'
                        .format(teacher['userId'],
                        teacher['course_id']))
                except HttpError as e:
                    error = simplejson.loads(e.content).get('error')
                    if(error.get('code') == 409):
                        print(u'User "{0}" is already a member of this course.').format(
teacher['userId'])
                    else:
                        raise

                # XXX Add students to course

        return render_template('success.html')

@app.route('/read')
def read():
    with open('test_courses.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        return render_template('courses.html', courses=reader)

@app.route('/upload', methods=['POST'])
def upload():
    # Get the name of the uploaded file
    file = flask.request.files['file']
    # Check if the file is one of the allowed types/extensions
    if file and allowed_file(file.filename):
        # Make the filename safe, remove unsupported chars
        # filename = secure_filename(file.filename)
        # Move the file form the temporal folder to
        # the upload folder we setup
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'courses_list.csv'))
        # Redirect the user to the uploaded_file route, which
        # will basicaly show on the browser the uploaded file
        return flask.redirect(flask.url_for('index'))


@app.route('/oauth2callback')
def oauth2callback():
    scopes = ['https://www.googleapis.com/auth/classroom.courses', 'https://www.googleapis.com/auth/classroom.rosters']
    flow = client.flow_from_clientsecrets(
        'client_secret.json',
        scopes,
        redirect_uri=flask.url_for('oauth2callback', _external=True))
    if 'code' not in flask.request.args:
        auth_uri = flow.step1_get_authorize_url()
        return flask.redirect(auth_uri)
    else:
        auth_code = flask.request.args.get('code')
        credentials = flow.step2_exchange(auth_code)
        flask.session['credentials'] = credentials.to_json()
        return flask.redirect(flask.url_for('index'))


application = app
