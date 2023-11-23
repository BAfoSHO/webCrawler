import sqlite3
from config import DATABASE_PATH

db_file = DATABASE_PATH

def create_connection():
    """ Create a database connection to the SQLite database specified by db_file """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
    except sqlite3.Error as e:
        print(e)
    return conn


def create_table(conn, create_table_sql):
    """ Create a table from the create_table_sql statement """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except sqlite3.Error as e:
        print(e)


def insert_cookie_data(conn, cookie_data):
    """ Insert a new row into the cookies table """
    sql = '''INSERT INTO cookies(url, name, value, domain, path, expires, http_only, secure, first_party)
              VALUES(?,?,?,?,?,?,?,?,?)'''
    try:
        cur = conn.cursor()
        cur.execute(sql, cookie_data)
        conn.commit()
        return cur.lastrowid
    except sqlite3.Error as e:
        print(f"Error inserting cookie data: {e}")


def insert_research_data(conn, research_data):
    """ Insert a new row into the research_data table """
    sql = '''INSERT INTO research_data(search_term, url, title, content)
              VALUES(?,?,?,?)'''
    try:
        cur = conn.cursor()
        cur.execute(sql, research_data)
        conn.commit()
        return cur.lastrowid
    except sqlite3.Error as e:
        print(f"Error inserting research data: {e}")


def init_db(db_file):
    # SQL statement for creating the cookies table
    sql_create_cookies_table = """
    CREATE TABLE IF NOT EXISTS cookies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL,
        name TEXT NOT NULL,
        value TEXT,
        domain TEXT,
        path TEXT,
        expires TEXT,
        http_only BOOLEAN,
        secure BOOLEAN,
        first_party BOOLEAN,
        retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """


    # SQL statement for creating the research_data table
    sql_create_research_table = """
    CREATE TABLE IF NOT EXISTS research_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        search_term TEXT NOT NULL,
        url TEXT NOT NULL,
        title TEXT,
        content TEXT,
        retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """


    # create a database connection
    conn = create_connection(db_file)
    if conn is not None:
        # create cookies table and research_data table
        create_table(conn, sql_create_cookies_table)
        create_table(conn, sql_create_research_table)
        conn.close()
    else:
        print("Error! cannot create the database connection.")
