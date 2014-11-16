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
    
    Either a welcome landing page with a login link or redirect to user's home.
    '''
    
    if 'username' in session:
        return redirect(url_for('home', username=session['username']))
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
def home(username):
    '''
    Logged in user's home page.
    
    Check if we've saved a Smarterer access token saved for the user.
    If not, provide a link for them to authorize with smarterer. If so, 
    show the embedded test widget. (See templates/home.html.)
    '''
    name = escape(username)

    conn = sqlite3.connect('example_leaderboard.db')
    c = conn.cursor()
    c.execute("SELECT access_token FROM user_tokens WHERE username=?",
                                                                (name,))
    is_authorized = bool(c.fetchone())
    conn.close()
    
    # Build the OAuth URL for the Authorize with Smarterer Link.
    api = smarterer.api.Smarterer(client_id=config.SMARTERER_CLIENT_ID)
    oauth_url = api.authorize_url()

    return render_template('home.html', username=name,
                                        oauth_url=oauth_url,
                                        is_authorized=is_authorized,
                                        widget_embed=config.SMARTERER_WIDGET_EMBED)


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
    

@app.route('/leaderboard')
def leaderboard():
    '''
    The leaderboard.

    If there's a logged in user, first ensure that her/his score has been saved 
    (or updated) in the database.

    Then pull the stored user test scores from the db and sort them.
    '''

    # Check for logged in user and insert/refresh score in db if so.
    if 'username' in session:
        username = escape(session['username'])
        util.update_badges(username)
    else:
        username = None

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
    return render_template('leaderboard.html', badges=badges, username=username)




# set the secret key.  keep this really secret:
app.secret_key = config.SECRET_KEY


if __name__ == "__main__":
    app.run(debug=True)
