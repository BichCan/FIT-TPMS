import sqlite3
import os

db_path = "FIT-TPMS.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users';")
    print(cursor.fetchone()[0])
    
    cursor.execute("SELECT DISTINCT role FROM users;")
    roles = cursor.fetchall()
    print("Roles found:", [r[0] for r in roles])
    conn.close()
else:
    print(f"File {db_path} not found.")
