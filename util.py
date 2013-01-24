import sqlite3
import smarterer.api

import config

def init():
    conn = sqlite3.connect('example_leaderboard.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE user_tokens
             (username TEXT PRIMARY KEY, access_token text)''')
    c.execute('''CREATE TABLE user_badges
     (username TEXT PRIMARY KEY, test_id INTEGER, score REAL, badge_url TEXT)''')
    conn.commit()
    conn.close()
    print "DATABASE CREATED"

def update_badges(username=None):
    conn = sqlite3.connect('example_leaderboard.db')
    c = conn.cursor()
    if username:
        c.execute("SELECT * FROM user_tokens WHERE username=?", (username,))
    else:
        c.execute("SELECT * FROM user_tokens")
    for username, access_token in c.fetchall():
        s = smarterer.api.Smarterer(client_id=config.SMARTERER_CLIENT_ID,
                                  client_secret=config.SMARTERER_APP_SECRET,
                                  verify=False,
                                  access_token=access_token)
        data = s.badges()
        print data
        for badge in data['badges']:
            try:
                c.execute("INSERT INTO user_badges VALUES (?, ?, ?, ?)",
                         (username,
                          badge[u'quiz'][u'id'],
                          badge[u'badge'][u'raw_score'],
                          badge[u'badge'][u'image']))
            except sqlite3.IntegrityError:
                c.execute("UPDATE user_badges SET test_id=?, score=?, badge_url=? WHERE username=?",
                        (badge[u'quiz'][u'id'],
                         badge[u'badge'][u'raw_score'],
                         badge[u'badge'][u'image'],
                         username))
    conn.commit()
    conn.close()
