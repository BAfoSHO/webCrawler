import csv
import sqlite3
from config import DATABASE_PATH


def export_cookies_to_csv(db_path, csv_file_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM cookies")
    rows = cursor.fetchall()

    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.writer(csv_file)
        # Writing column headers
        csv_writer.writerow([i[0] for i in cursor.description])
        # Writing data rows
        csv_writer.writerows(rows)

    conn.close()

if __name__ == "__main__":
    export_cookies_to_csv(DATABASE_PATH, 'cookies_export.csv')

