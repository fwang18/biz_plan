import datetime
import psycopg2


def insert_users(id, name, email, subscriber, sessions_to_date):
    """
    This function inserts a row of new user information
    """
    SQLCursor = LCLconnR.cursor()
    SQLCursor.execute(
        """
        INSERT INTO picturesque.users
        (id, name, email, subscriber, sessions_to_date)
        VALUES (%s, %s, %s, %s, %s);
        """, (id, name, email, subscriber, sessions_to_date))

    LCLconnR.commit()


def insert_sessions(id, ts, photos, free_trials_remaining):
    """
    This function inserts a row of new session information
    """
    SQLCursor = LCLconnR.cursor()
    SQLCursor.execute(
        """
        INSERT INTO picturesque.sessions
        (id, ts, photos, free_trials_remaining)
        VALUES (%s, %s, %s, %s);
        """, (id, ts, photos, free_trials_remaining))

    LCLconnR.commit()


# Demo
v1 = 'xyz'
v2 = 'chen'
v3 = 'cwang98@usfca.edu'
v4 = 0
v5 = 0

ts = datetime.datetime.now()
photos = 5
free_trials_remaining = 3

LCLconnR = psycopg2.connect("dbname='msan691' host='localhost'")
insert_users(v1, v2, v3, v4, v5)
insert_sessions(id=v1, ts=ts, photos=photos,
                free_trials_remaining=free_trials_remaining)
