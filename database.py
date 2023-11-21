import sqlite3


def create_connection(db_file):
    """ Create a database connection to the SQLite database specified by db_file """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
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


    # create a database connection
    conn = create_connection(db_file)
    if conn is not None:
        # create cookies table
        create_table(conn, sql_create_cookies_table)
        conn.close()
    else:
        print("Error! cannot create the database connection.")

