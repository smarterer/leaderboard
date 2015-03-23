from flask import (Flask, session, redirect, url_for, escape,
                   request, render_template, send_from_directory)
from flask.ext.sqlalchemy import SQLAlchemy

import smarterer.api
import sqlite3
import config
import requests
import sqlalchemy


app = Flask(__name__, static_url_path='')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example_leaderboard.db'
db = SQLAlchemy(app)

class Score(db.Model):
    __tablename__ = "scores"
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship("User", backref=db.backref("score", uselist=False))
    # quiz_id = db.Column(db.Integer)
    _value = db.Column("value", db.Integer)
    date_created = db.Column(db.TIMESTAMP,
                                 default=db.func.current_timestamp())

    @property
    def display_value(self):
        '''Return the score with additional precision.'''
        return int(round(self.value))

    @property
    def value(self):
        '''Return the score with additional precision.'''
        return self._value / 1000.0

    @value.setter
    def value(self, value):
        '''Set the score, convert to an int at 1000x.'''
        self._value = int(round(value * 1000.0))

    def __repr__(self):
        return "<Score(id='{0}', quiz='{1}', score='{2}')>".format(self.id,
                                                     self.quiz_id, self.value)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    username = db.Column(db.Unicode(40), unique=True, key='username')
    email = db.Column(db.Unicode(255), unique=True, key='email')
    first_name = db.Column(db.Unicode(255))
    last_name = db.Column(db.Unicode(255))
    profile_image = db.Column(db.Unicode(511))
    access_token = db.Column(db.Unicode(40), unique=True)
    date_created = db.Column(db.TIMESTAMP,
                                 default=db.func.current_timestamp())
    last_sync = db.Column(db.TIMESTAMP,
                                 default=db.func.current_timestamp())
    can_login = True

    @property
    def display_name(self):
        if self.first_name and self.last_name:
            return " ".join([self.first_name, self.last_name])
        elif self.first_name:
            return self.first_name
        else:
            return self.username

    def __repr__(self):
        return "<User('%s', '%s')>" % (self.id, self.username)


@app.route("/")
def index():
    '''
    Front page.

    Either a welcome landing page with a login link or redirect to profile page.
    '''
    if "username" in session:
        username = escape(session['username'])
        user = db.session.query(User).filter_by(username=username).one()
    else:
        user = None
    scores = (db.session.query(Score).order_by(db.desc(Score._value)).limit(20).
                      all())
    return render_template('leaderboard.html',
                             user=user, scores=scores,
                             SMARTERER_CLIENT_ID=config.SMARTERER_CLIENT_ID)


@app.route('/reg_complete', methods=['GET'])
def smarterer_callback():
    '''
    Create a new user
    '''
    auth_code = request.args.get("code") or 'NO CODE'

    params = {'client_id': config.SMARTERER_CLIENT_ID,
              'client_secret': config.SMARTERER_APP_SECRET,
              'code': auth_code,
              'grant_type': 'authorization_code'
              }
    resp = requests.get('https://smarterer.com/oauth/access_token',
                        params=params,
                        verify=False)

    token = resp.json().get('access_token')
    if token:
        params = {'access_token': token}
        resp = requests.get('https://smarterer.com/api/users/me',
                            params=params, verify=False)
        prof_data = resp.json()
        try:
            user = db.session.query(User).filter_by(username=prof_data['username']).one()
        except sqlalchemy.orm.exc.NoResultFound:
            user_keys = ("username", "email", "first_name", "last_name", "profile_image")
            params = dict([(key, value) for key, value in prof_data.items() if key in user_keys and value is not None])
            params['access_token'] = token
            user = User(**params)
            db.session.add(user)
            db.session.commit()
        session['username'] = user.username
        return redirect(url_for('sync'))

    else:
        return redirect(url_for('index'))



def sync_scores(user):
    params = {'access_token': user.access_token,
              'tests': '80s-trivia'}
    resp = requests.get('https://smarterer.com/api/badges',
                        params=params,
                        verify=False)
    if resp.status_code != 200:
        return False
    score_data = resp.json()
    if score_data.get('badges', []):
        raw_score = score_data['badges'][0]['badge']['raw_score']
    else:
        return False

    if user.score:
        user.score.value = raw_score
    else:
        user.score = Score(value=raw_score)
    return True


def sync_profile(user):
    params = {'access_token': user.access_token}
    resp = requests.get('https://smarterer.com/api/users/me',
                        params=params, verify=False)
    if resp.status_code != 200:
        return False
    prof_data = resp.json()
    user_keys = ("username", "first_name", "last_name", "profile_image")
    for key in user_keys:
        if prof_data.get(key, None) is not None:
            setattr(user, key, prof_data[key])


@app.route('/sync')
def sync():
    '''
    sync profiles
    '''
    if "username" in session:
        username = escape(session['username'])
        user = db.session.query(User).filter_by(username=username).one()
    if user:
        sync_scores(user)
        sync_profile(user)
        db.session.commit()
    return redirect(url_for('index'))


@app.route('/80s')
def test_show():
    if "username" in session:
            username = escape(session['username'])
            user = db.session.query(User).filter_by(username=username).one()
    else:
        user = None
    return render_template('show_test.html',
                         user=user)

@app.route('/80s/run')
def run():
    if "username" in session:
            username = escape(session['username'])
            user = db.session.query(User).filter_by(username=username).one()
    else:
        user = None
    if not user:
        return redirect(url_for('index'))

    return render_template('run_test.html',
                            user=user)


@app.route('/logout')
def logout():
    '''
    Logout: remove the username from the session if it's there
    '''
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('js', path)

@app.route('/css/<path:path>')
def send_css(path):
    return send_from_directory('css', path)

@app.route('/img/<path:path>')
def send_img(path):
    return send_from_directory('img', path)


# set the secret key.  keep this really secret:
app.secret_key = config.SECRET_KEY


if __name__ == "__main__":
    app.run(debug=True)
