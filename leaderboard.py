from flask import (Flask, session, redirect, url_for, escape,
                   request, render_template)
import smarterer.api
import sqlite3
import util
import config

app = Flask(__name__)

@app.route("/")
def index():
    '''
    Front page.
    
    Either a welcome landing page with a login link or redirect to profile page.
    '''
    
    if 'username' in session:
        return redirect(url_for('profile', username=session['username']))
    else:
        api = smarterer.api.Smarterer(client_id=config.SMARTERER_CLIENT_ID)
        oauth_url = api.authorize_url()
        return render_template('welcome.html', username=None,
                                            oauth_url=oauth_url,
                                            authd=False,
                                            widget_embed=config.SMARTERER_WIDGET_EMBED)


@app.route('/login', methods=['GET', 'POST'])
def login():
    '''
    Login: show or handle the login form.
    '''
    if request.method != 'POST':
        # just render the login form for a GET request.
        return render_template('login.html')
    else:
        # handle the login: for this example just naively save the username
        # in the session and then redirect.
        session['username'] = request.form['username']
        return redirect(url_for('index'))


@app.route('/logout')
def logout():
    '''
    Logout: remove the username from the session if it's there
    '''
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route('/user/<username>')
def profile(username):
    '''
    Profile page /user/<username>
    
    Grab the stored Leaderboard score info for <username> from the db.

    If <username> is not the currently logged in user, then just use that info
    to render a public profile page.

    If <username> IS the currently logged in user:
        1. Check if we've saved an access token saved for the user.
        2. If not, then ask the her to authorize on Smarterer.
        3. Otherwise, pull down her most up to date score from Smarterer using 
           the /badges REST endpoint.
        4. Give the user a way to update the leaderboard with their latest score
           if it's different. (See profile.html and the update() function.)        
    '''

    name = escape(username)
    conn = sqlite3.connect('example_leaderboard.db')
    
    # Look in our db for stored Leaderboard test result for the owner of this
    # profile.
    c = conn.cursor()
    c.execute("SELECT * FROM user_badges WHERE test_url_slug=? AND username=?",
                                                        (config.TEST_URL_SLUG,
                                                        name))
    leaderboard_badge = c.fetchone()
    
    # Is this the profile of the currently logged-in user?
    if session.get('username') != username:
        # If not, then we're done: it's a simple profile page.
        conn.close()
        return render_template('public_profile.html', username=name,
                                            leaderboard_badge=leaderboard_badge)

    #
    # Otherwise, it's the current user's profile page:
    #
    
    # Get the stored access token for the owner of this profile.
    c = conn.cursor()
    c.execute("SELECT access_token FROM user_tokens WHERE username=?", (name,))
    access_token = c.fetchone()
    conn.close()

    
    # If we don't have an access token, then ask them to authorize
    # with Smarterer.
    if not access_token:
        return please_authorize(name)

    # On the other hand, if the logged in user own this profile and they HAVE
    # authorized, then grab their most up-to-date test results (if any) from
    # Smarterer.
    s = smarterer.api.Smarterer(client_id=config.SMARTERER_CLIENT_ID,
                              client_secret=config.SMARTERER_APP_SECRET,
                              verify=False,
                              access_token=access_token)
    
    data = s.badges((config.TEST_URL_SLUG,))
    
    smarterer_result = None
    if len(data['badges']) > 0:
        smarterer_result = data['badges'][0]
        
    return render_template('profile.html', username=name,
                                        smarterer_result=smarterer_result,
                                        leaderboard_badge=leaderboard_badge,
                                        widget_embed=config.SMARTERER_WIDGET_EMBED
                                        )


def please_authorize(name):
    '''
    We need to ask user to authorize with Smarterer.
    Build the OAuth URL for the Authorize with Smarterer Link.
    '''
    api = smarterer.api.Smarterer(client_id=config.SMARTERER_CLIENT_ID)
    oauth_url = api.authorize_url()

    return render_template('please_authorize.html', username=name,
                                        oauth_url=oauth_url)

@app.route('/smarterer_auth_complete')
def auth_complete():
    '''
    This is the OAuth callback handler.  After we send the user to Smarterer
    and s/he authorizes access, Smarterer redirects her/him back to this URL
    with a temporary `code` query parameter, which we use to get the longer-
    term access token for this user that we'll save in the db so that our app
    can continue to access the user's Smarterer data.
        
    (Recall that we configured this particular URL when we registered the
    Leaderboard app with Smarterer.)
    '''
    username = session.get('username', None)
    if not username:
        return redirect(url_for('login'))
    api = smarterer.api.Smarterer(client_id=config.SMARTERER_CLIENT_ID,
                                  client_secret=config.SMARTERER_APP_SECRET,
                                  verify=False)
    access_token = api.get_access_token(code=request.args.get('code', ''))

    conn = sqlite3.connect('example_leaderboard.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO user_tokens VALUES (?, ?)", (username, access_token))
    except sqlite3.IntegrityError:
        c.execute("UPDATE user_tokens SET access_token=? WHERE username=?", (access_token, username))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))
    
    
@app.route('/update')
def update():
    '''
    Respond to the user's request to post her most recent Smarterer score to
    the leaderboard.
    '''

    username = escape(session['username'])
    if not username:
        return redirect(url_for('index'))
        
    conn = sqlite3.connect('example_leaderboard.db')
    c = conn.cursor()
    c.execute("SELECT * FROM user_tokens WHERE username=?", (username,))
    access_token = c.fetchone()

    s = smarterer.api.Smarterer(client_id=config.SMARTERER_CLIENT_ID,
                              client_secret=config.SMARTERER_APP_SECRET,
                              verify=False,
                              access_token=access_token)

    data = s.badges((config.TEST_URL_SLUG,))
    for badge in data['badges']:
        try:
            c.execute("INSERT INTO user_badges VALUES (?, ?, ?, ?)",
                     (username,
                      badge[u'quiz'][u'url_slug'],
                      badge[u'badge'][u'raw_score'],
                      badge[u'badge'][u'image']))
        except sqlite3.IntegrityError:
            c.execute("UPDATE user_badges SET test_url_slug=?, score=?, badge_url=? WHERE username=?",
                    (badge[u'quiz'][u'url_slug'],
                     badge[u'badge'][u'raw_score'],
                     badge[u'badge'][u'image'],
                     username))
    conn.commit()
    conn.close()

    return redirect(url_for('leaderboard'))


@app.route('/leaderboard')
def leaderboard():
    '''
    The leaderboard.

    If there's a logged in user, first ensure that her/his score has been saved 
    (or updated) in the database.

    Then pull the stored user test scores from the db and sort them.
    '''

    # Pull scores from db and render the sorted list.
    conn = sqlite3.connect('example_leaderboard.db')
    c = conn.cursor()
    c.execute("SELECT * FROM user_badges WHERE test_url_slug=?", (config.TEST_URL_SLUG,))
    d = [{'username': badge_username, 
        'test_url_slug': test_url_slug,
        'raw_score': raw_score,
        'badge_image': badge_image} for (badge_username, test_url_slug, raw_score, badge_image) in c.fetchall()]
    conn.close()
    badges = sorted(d, key=lambda badge: badge['raw_score'], reverse=True)
    return render_template('leaderboard.html', badges=badges, username=session.get('username'))




# set the secret key.  keep this really secret:
app.secret_key = config.SECRET_KEY


if __name__ == "__main__":
    app.run(debug=True)
