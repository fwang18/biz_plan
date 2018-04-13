import os, psycopg2

# Note that it is assumed that we already have the database connected
# before calling all the SQL-related statements

def create_schema(schema_name='picturesque'):
    """
    This function allows the user to specify the name of
    the schema to be created and create it accordingly
    """
    SQLCursor = LCLconnR.cursor()

    # drop schema if already exists
    SQLCursor.execute(
        """
        drop schema if exists %s CASCADE;
        commit;
        """ % schema_name)

    # create new schema
    SQLCursor.execute(
        """
        CREATE SCHEMA %s;
        """ % schema_name)

    LCLconnR.commit()


def create_users_table(schema_name ='picturesque', table_name ='users'):
    """
    This function is to create the users table - note that this may
    be modified according to our needs
    """
    SQLCursor = LCLconnR.cursor()
    SQLCursor.execute(
        """
        CREATE TABLE %s.%s
        (id varchar(15), 
        name varchar(10),
        email varchar(30),
        subscriber int,
        sessions_to_date int);
        """ % (schema_name, table_name))

    LCLconnR.commit()


def create_sessions_table(schema_name='picturesque', table_name='sessions'):
    """
    This function is to create the sessions table - note that this may
    be modified according to our needs
    """
    SQLCursor = LCLconnR.cursor()

    SQLCursor.execute(
        """
       CREATE TABLE %s.%s
       (id varchar(15), 
       ts timestamp,
       photos int,
       free_trials_remaining int);
       """ % (schema_name, table_name))

    LCLconnR.commit()


def copy_csv_table(file_dir, filename, table_name, schema_name = 'picturesque'):
    """
    This function copies the content in a csv file to the designated table
    """
    SQLCursor = LCLconnR.cursor()

    SQLCursor.execute(
        """
        COPY %s.%s FROM '%s' CSV;
        """ % (schema_name, table_name, file_dir + filename))

    LCLconnR.commit()

# Demo:

schema = 'picturesque'
users_table = 'users'
sessions_table = 'sessions'

log_dir = os.getcwd()+'/sample_csv/'
users_file = 'users.csv'
sessions_file = 'sessions.csv'


LCLconnR = psycopg2.connect("dbname='msan691' host='localhost'")

create_schema()
create_users_table()
create_sessions_table()
copy_csv_table(file_dir=log_dir, filename=users_file, table_name=users_table)
copy_csv_table(file_dir=log_dir, filename=sessions_file, table_name=sessions_table)