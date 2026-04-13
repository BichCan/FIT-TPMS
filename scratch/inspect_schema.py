import sqlite3
import os

db_path = r'd:\FIT-TPMS\FIT-TPMS\FIT-TPMS.db'

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    tables = ['lecturers', 'classes', 'users']
    for table in tables:
        print(f"\n--- Schema for {table} ---")
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        for col in columns:
            print(col)
    
    conn.close()
