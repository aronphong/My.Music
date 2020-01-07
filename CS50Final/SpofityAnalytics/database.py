import sqlite3
from sqlite3 import Error

def create_connection(db_file):
    """ Create a database connection to a SQLite database """

    conn = None

    try: 
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
    except Error as e:
        print(e)

    return conn 


def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: connection object
    :param create_table_Sql: a CREATE TABLE statement
    :return:
    """

    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def add_user(conn, users, username, hashpw):
    """ 
    Create a new user row into the users table
    :param conn:
    :param users:
    :param username:
    :param hashpw:
    :return: project id
    """ 

    sql = """ INSERT INTO users(username, hash), username=:username, hash=:hashpw """
    cur = conn.cursor()
    cur.execute(sql, users)
    return cur.lastrowid 

def main():
    database = "mymusic.db"

    sql_create_users_table = """ CREATE TABLE IF NOT EXISTS users (
                                    id integer PRIMARY KEY,
                                    username text,
                                    hashpw text
                                 ); """

    # create a database connection
    conn = create_connection(database)

    # create tables
    if conn is not None:
        # create users table
        create_table(conn, sql_create_users_table)
    else:
        print("Error! cannot create db connection.")


if __name__ == '__main__':
    main()