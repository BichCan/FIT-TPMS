import sqlite3
import os

db_path = "FIT-TPMS.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    with open("schema_dump.txt", "w", encoding="utf-8") as f:
        for table in tables:
            f.write(f"--- Table: {table[0]} ---\n")
            cursor.execute(f"PRAGMA table_info({table[0]});")
            info = cursor.fetchall()
            for col in info:
                f.write(str(col) + "\n")
    conn.close()
    print("Schema dumped to schema_dump.txt")
else:
    print("Database not found")
