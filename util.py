import sqlite3
import smarterer.api

import config

def init():
    conn = sqlite3.connect('example_leaderboard.db')
    c = conn.cursor()
    c.execute('''DROP TABLE IF EXISTS user_tokens''')
    c.execute('''CREATE TABLE user_tokens
             (username TEXT PRIMARY KEY, access_token text)''')
    c.execute('''DROP TABLE IF EXISTS user_badges''')
    c.execute('''CREATE TABLE user_badges
     (username TEXT PRIMARY KEY, test_url_slug TEXT, score REAL, badge_url TEXT)''')
    conn.commit()
    conn.close()
    print "DATABASE TABLES CREATED / DROPPED AND RECREATED"

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2:
        if sys.argv[1] == 'init':
            init()
