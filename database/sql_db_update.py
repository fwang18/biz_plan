import datetime
import psycopg2


# Note that we may need to write different functions to
# update different pieces of the record. I only give an
# example template here


def update_subscriber(id, subscriber_boolean):
    SQLCursor = LCLconnR.cursor()
    SQLCursor.execute(
        """
        UPDATE picturesque.users SET subscriber=%s where id=%s;
        """, (subscriber_boolean, id))
    LCLconnR.commit()


# Demo:

subscriber = 1
id = 'abc'
LCLconnR = psycopg2.connect("dbname='msan691' host='localhost'")
update_subscriber(id=id, subscriber_boolean=subscriber)
