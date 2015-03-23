from leaderboard import db

def init():
    db.create_all()
    print "DATABASE TABLES CREATED / DROPPED AND RECREATED"

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2:
        if sys.argv[1] == 'init':
            init()
