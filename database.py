import sqlite3
from config import DATABASE_PATH


def create_connection(db_path):
    # Create database connection to SQLite database specified by db_path
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except sqlite3.Error as e:
        print(f"Error creating database connection: {e}")
        return None


def create_table(conn, create_table_sql):\
    # Create a table from the create_table_sql statement
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
        conn.commit()
        print("Table created successfully.")  # Debug print
    except sqlite3.Error as e:
        print(f"Error creating table: {e}")  # Error print


def insert_cookie_data(conn, cookie_data):
    # Insert a new row into the cookies table
    sql = '''INSERT INTO cookies(url, name, value, domain, path, expires, http_only, secure, first_party)
              VALUES(?,?,?,?,?,?,?,?,?)'''
    with conn:
        try:
            cur = conn.cursor()
            cur.execute(sql, cookie_data)
            return cur.lastrowid
        except sqlite3.Error as e:
            print(f"Error inserting cookie data: {e}")


def insert_research_data(conn, research_data):
    # Insert a new row into the research_data table
    sql = '''INSERT INTO research_data(search_term, url, title, content)
              VALUES(?,?,?,?)'''
    with conn:
        try:
            cur = conn.cursor()
            cur.execute(sql, research_data)
            return cur.lastrowid
        except sqlite3.Error as e:
            print(f"Error inserting research data: {e}")


def init_db():
    cookies_table_sql = """
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

    research_data_table_sql = """
    CREATE TABLE IF NOT EXISTS research_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        search_term TEXT NOT NULL,
        url TEXT NOT NULL,
        title TEXT,
        content TEXT,
        retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    print("Initializing database...")
    conn = create_connection(DATABASE_PATH)
    if conn:
        print("Creating tables...")
        create_table(conn, cookies_table_sql)
        create_table(conn, research_data_table_sql)
        conn.close()
        print("Tables created successfully.")
    else:
        print("Error! Cannot create the database connection.")

if __name__ == "__main__":
    init_db()

