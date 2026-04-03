import sqlite3
import os

db_path = "FIT-TPMS.db"
out_path = "inspect_results.txt"

try:
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get schema
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users';")
        schema = cursor.fetchone()[0]
        
        # Get roles
        cursor.execute("SELECT DISTINCT role FROM users;")
        roles = cursor.fetchall()
        
        # Get one sample user (excluding password)
        cursor.execute("SELECT id, username, email, role FROM users LIMIT 5;")
        users = cursor.fetchall()
        
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(f"SCHEMA:\n{schema}\n\n")
            f.write(f"ROLES FOUND:\n{str([r[0] for r in roles])}\n\n")
            f.write(f"SAMPLE USERS:\n{str(users)}\n")
        
        print("Success")
        conn.close()
    else:
        print(f"File {db_path} not found.")
except Exception as e:
    with open(out_path, "w") as f:
        f.write(f"ERROR: {str(e)}")
    print(f"Error: {str(e)}")
