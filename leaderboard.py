from flask import (Flask, session, redirect, url_for, escape,
                   request, render_template)
import smarterer.api
import sqlite3
import util
import config

app = Flask(__name__)

@app.route("/")
def index():
    if 'username' in session:
        name = escape(session['username'])
        conn = sqlite3.connect('example_leaderboard.db')
        c = conn.cursor()
        c.execute("SELECT access_token FROM user_tokens WHERE username=?",
                                                                    (name,))
        t = c.fetchone()
        conn.close()
    else:
        name = None
        t = None
    api = smarterer.api.Smarterer(client_id=config.SMARTERER_CLIENT_ID)
    oauth_url = api.authorize_url(callback="localhost:5000/")
    return render_template('welcome.html', username=name,
                                        oauth_url=oauth_url,
                                        authd=bool(t),
                                        widget_embed=config.SMARTERER_WIDGET_EMBED)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['username'] = request.form['username']
        return redirect(url_for('index'))
    return render_template('login.html')
    # return '''
    #     <form action="" method="post">
    #         <p>Type a username to log in: <input type="text" name="username"></p>
    #         <p><input type=submit value=Login></p>
    #     </form>
    # '''


@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route('/leaderboard')
def leaderboard():
    if 'username' in session:
        username = escape(session['username'])
        util.update_badges(username)
    else:
        username = None

    conn = sqlite3.connect('example_leaderboard.db')
    c = conn.cursor()
    c.execute("SELECT * FROM user_badges WHERE test_id=?", (config.TEST_ID,))
    d = [{'username': badge_username, 
        'test_id': test_id,
        'raw_score': raw_score,
        'badge_image': badge_image} for (badge_username, test_id, raw_score, badge_image) in c.fetchall()]
    conn.close()
    badges = sorted(d, key=lambda badge: badge['raw_score'], reverse=True)
    return render_template('leaderboard.html', badges=badges, username=username)


@app.route('/smarterer_auth_complete')
def auth_complete():
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

# set the secret key.  keep this really secret:
app.secret_key = config.SECRET_KEY


if __name__ == "__main__":
    app.run(debug=True)


