import sqlite3
import os

db_path = "FIT-TPMS.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for table in tables:
        print(f"--- Table: {table[0]} ---")
        cursor.execute(f"PRAGMA table_info({table[0]});")
        info = cursor.fetchall()
        for col in info:
            print(col)
    conn.close()
else:
    print("Database not found")
